"""
This script goes through the SPICE data and finds time
intervals LRO DIVINER is within area of interests
"""

import os
import logging
from typing import Optional
import sys

sys.path.insert(0, "/".join(__file__.split("/")[:-4]))

import pandas as pd
import numpy as np
from astropy.time import Time, TimeDelta
import spiceypy as spice

from scipy.spatial.distance import euclidean

from src.scripts.SPICE.instruments import DIVINERInstrument
from src.scripts.SPICE.config import (
    TIME_STEP,
    DESTINATION,
    LONE_KERNELS,
    LUNAR_MODEL,
    MOON_STR_ID,
    LRO_SPEED,
    QUERY_RADIUS,
)

from tqdm import tqdm

from src.db.mongo.interface import Sessions
from src.scripts.SPICE.dynamic_kernel_loader import DynamicKernelLoader

points = Sessions.get_all_pits_points()


class SweepIterator:
    """
    This SweepIterator ensures we have correct SPICE files loaded for given datetime
    """

    @property
    def min_loaded_time(self):
        return max([kernel.min_loaded_time for kernel in self.dynamic_kernels])

    @property
    def max_loaded_time(self):
        return min([kernel.max_loaded_time for kernel in self.dynamic_kernels])

    def __init__(self):
        """Loads all SPICE metadata"""
        # Load larger dynamically loaded SPICE kernels
        self.dynamic_kernels = [
            DynamicKernelLoader("ck/lrodv", "ck", startswith="lrodv"),  # Radiometer position
            DynamicKernelLoader("ck/lrosc", "ck", startswith="lrosc"),  # LRO position (probably)
            DynamicKernelLoader("spk", "spk"),
        ]

        # Load smaller static SPICE kernels
        def compose_kernel_path(folder, suffix: str):
            if folder is not None:
                file_path = os.path.join(DESTINATION, folder)
            else:
                file_path = DESTINATION

            return [os.path.join(file_path, kernel) for kernel in os.listdir(file_path) if kernel.endswith(suffix)]

        kernel_args = [
            ("sclk", ".tsc"),
            ("spk", ".bsp"),
            ("ik", ".ti"),
            ("fk", ".tf"),
            ("lsk", ".tls"),
            ("pck", ".bpc"),
            (None, ".bpc"),  # None means in root of the SPICE kernel folder
            (None, ".bsp"),
            (None, ".dsk"),
        ]

        kernels = [kernel for args in kernel_args for kernel in compose_kernel_path(*args)]

        for kernel in tqdm(kernels, ncols=200, desc="Loading static SPICE kernels from folders"):
            spice.furnsh(kernel)

        for kernel in tqdm(LONE_KERNELS, ncols=200, desc="Loading lone SPICE kernels from files"):
            spice.furnsh(kernel["path"])

        logging.info("Loading detailed model of the Moon")
        spice.furnsh(LUNAR_MODEL["dsk_path"])

    def step(self, time: Time):
        return all([kernel.refresh_SPICE_for_given_time(time) for kernel in self.dynamic_kernels])

    def initiate_sweep(self, starting_datetime: Time):
        all_loaded = self.step(starting_datetime)

        if not all_loaded:
            raise ValueError("Some of dynamic SPICE kernels were not loaded for required time")


class Sweeper:
    # TODO: Will have to work on some step tolerance of distance covered in the timestep interval
    _points = None

    @property
    def points(self):
        if not self._points:
            self._points = Sessions.get_all_pits_points()
        return self._points

    @property
    def min_time(self):
        return self.sweep_iterator.min_loaded_time

    @property
    def max_time(self):
        return self.sweep_iterator.max_loaded_time

    def __init__(self):
        # Load SPICE kernels, in order to compute other stuff with SPICE
        self.sweep_iterator = SweepIterator()
        # Setup simulation
        self.computation_timedelta = TimeDelta(TIME_STEP, format="sec")
        # Always remember to update both times!
        self.current_simulation_timestamp = self.min_time + self.computation_timedelta
        self.current_simulation_timestamp_et = spice.str2et(self.current_simulation_timestamp.utc.iso)
        self.current_simulation_step = 0

        # Load instrumets
        self.instruments = [
            DIVINERInstrument(),
        ]
        # Compute cartesian coordinates of points of interest
        self._points = self._get_crater_points_df()
        offset = max([instrument.offset_days for instrument in self.instruments])
        self._set_time(self.min_time + TimeDelta(offset, format="jd"))
        # Read time-dependant SPICE kernels
        self.sweep_iterator.initiate_sweep(self.current_simulation_timestamp)

        # Compute adjusted distance treshold - allows us to count with velocity and samp[ling frequency.
        self.distance_threshold_velocity_correction = ((TIME_STEP / 2) * LRO_SPEED + QUERY_RADIUS)


    def _step_time(self):
        self.current_simulation_timestamp += self.computation_timedelta
        self.current_simulation_timestamp_et = spice.str2et(self.current_simulation_timestamp.utc.iso)
        self.current_simulation_step += 1
        self.sweep_iterator.step(self.current_simulation_timestamp)

    def _set_time(self, time: Time, timestep: Optional[int] = None):
        self.current_simulation_timestamp = time
        self.current_simulation_timestamp_et = spice.str2et(self.current_simulation_timestamp.utc.iso)
        self.current_simulation_step = 0 if timestep is None else timestep
        self.sweep_iterator.step(self.current_simulation_timestamp)

    def _get_crater_points_df(self):
        points = Sessions.get_all_pits_points()
        latitudes_rad = points["latitude"] * spice.rpd()
        longitudes_rad = points["longitude"] * spice.rpd()

        cartesian_points = latitudes_rad.combine(
            longitudes_rad, lambda lat, lon: spice.srfrec(spice.bodn2c(MOON_STR_ID), lon, lat)
        )

        points["X"] = cartesian_points.apply(lambda xyz: xyz[0])
        points["Y"] = cartesian_points.apply(lambda xyz: xyz[1])
        points["Z"] = cartesian_points.apply(lambda xyz: xyz[2])

        return points


    def _compute_instrument_rays(self):
        """Compute FOVs on the Moon for givem time"""
        return {
            instrument.name: instrument.compute_rays(self.current_simulation_timestamp_et)
            for instrument in self.instruments
        }

    def _compute_fov_distances(self, fovs):
        """Computes distances between FOV of instruments and points we are looking for"""
        # List to store results
        results = []

        # Compute Euclidean distances
        for instrument, projections in fovs.items():
            for instrument_id, data in projections.items():
                boresight = data.boresight
                bounds = data.bounds

                for site_name, row in self._points.iterrows():
                    target_point = np.array([row["X"], row["Y"], row["Z"]])

                    # Compute distances for boresight
                    boresight_distance = euclidean(boresight, target_point)
                    results.append((instrument, instrument_id, "boresight", site_name, boresight_distance))

                    # Compute distances for bounds
                    for i, bound in enumerate(bounds):
                        bound_distance = euclidean(bound, target_point)
                        results.append((instrument, instrument_id, f"bound_{i+1}", site_name, bound_distance))

        # Convert results to DataFrame
        return pd.DataFrame(results, columns=["Instrument", "Instrument_ID", "Point_Type", "Moon_Feature", "Distance"])


    def _filter_point_distances(self, distances):
        """
        Filters the DataFrame to only include rows where the 'Distance' column is below the given threshold.

        :param df: Input DataFrame containing the 'Distance' column.
        :param threshold: Distance threshold for filtering.
        :return: Filtered DataFrame.
        """
        return distances[distances["Distance"] < self.distance_threshold_velocity_correction]


    def run_simulation(self, max_steps: Optional[int] = None):
        """
        Run simulation with uniform timestep.
        """
        total_seconds = (self.max_time - self.min_time).to_value("sec")

        with tqdm(total=total_seconds, ncols=200, desc="Running simulation") as pbar:
            while self.current_simulation_timestamp <= self.max_time:

                try:

                    self._step_time()
                    pbar.update(TIME_STEP)

                    # Compute the FOVs of instruments
                    fovs = self._compute_instrument_rays()

                    # Compute distances from point (euclidean)
                    distances = self._compute_fov_distances(fovs, self._points)


                    if max_steps is not None and self.current_simulation_step >= max_steps:
                        break

                except Exception as e:
                    logging.error(f"An error occured at step {self.current_simulation_step}: {e}")
                    break
