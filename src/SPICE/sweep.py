"""
This script processes SPICE data to identify time intervals when LRO DIVINER
is within areas of interest.
"""
import logging
import sys
from typing import Optional

sys.path.insert(0, "/".join(__file__.split("/")[:-3]))

import numpy as np
from astropy.time import Time, TimeDelta
import spiceypy as spice
from tqdm import tqdm
from scipy.spatial import cKDTree

from src.global_config import TQDM_NCOLS
from src.SPICE.instruments import DIVINERInstrument
from src.SPICE.config import TIME_STEP, MOON_STR_ID, LRO_SPEED, MAX_TIME_STEP
from src.db.mongo.interface import Sessions
from src.SPICE.sweep_iterator import SweepIterator

logger = logging.getLogger(__name__)


class Sweeper:
    """
    Iterates through SPICE data to update instrument distances to areas of interest,
    adjusts simulation timesteps, and records detections (points of interest) into MongoDB.

    For each simulation step:
      1. It projects the instrument’s boresight to get a first set of feasible target points.
      2. It then computes sub-instrument boresight projections and uses these to compute distances
         from each sub-instrument to the feasible points.
      3. If any sub-instrument yields a minimum distance below a defined (finer) threshold,
         the detection is recorded (with instrument name, simulation ET, best distance, and sub-instrument ID).
         
    """

    def __init__(self):
        self.sweep_iterator = SweepIterator()
        self.computation_timedelta = TimeDelta(TIME_STEP, format="sec")
        self.current_simulation_timestamp = self.sweep_iterator.min_loaded_time + self.computation_timedelta
        self.current_simulation_timestamp_et = spice.str2et(self.current_simulation_timestamp.utc.iso)
        self.current_simulation_step = 0

        # Load instruments
        self.instruments = [DIVINERInstrument()]

        # Get points of interest and build a KD-Tree for fast spatial searches
        self._load_target_points()

        # Set simulation start time considering instrument offset
        offset = max(instrument.offset_days for instrument in self.instruments)
        self._set_time(self.sweep_iterator.min_loaded_time + TimeDelta(offset, format="jd"))
        self.sweep_iterator.initiate_sweep(self.current_simulation_timestamp)

        # Tracking lists
        self._found_timestamps, self._found_timestamps_cnt = [], 0
        self._boresight_projections = []
        self._failed_timestamps, self._failed_timestamps_cnt = [], 0
        self.adjusted_timesteps = []
        self.min_distances = []

    @property
    def data(self):
        return {
            "found": self._found_timestamps,
            "failed": self._failed_timestamps,
            "adjusted_timesteps": self.adjusted_timesteps,
            "min_distances": self.min_distances,
            "boresight_projections": self._boresight_projections,
        }


    @property
    def min_time(self):
        return self.sweep_iterator.min_loaded_time

    @property
    def max_time(self):
        return self.sweep_iterator.max_loaded_time

    def _load_target_points(self):
        """Fetches crater points and converts lat/lon to Cartesian coordinates."""
        points = Sessions.get_all_pits_points()
        lat_rad = np.radians(points["latitude"])
        lon_rad = np.radians(points["longitude"])

        moon_id = spice.bodn2c(MOON_STR_ID)
        cartesian_points = np.array([spice.srfrec(moon_id, lon, lat) for lat, lon in zip(lat_rad, lon_rad)])

        points["X"], points["Y"], points["Z"] = cartesian_points.T
        self._target_points = points[["X", "Y", "Z"]].values
        self._target_ids = np.arange(len(self._target_points))
        self.kd_tree = cKDTree(self._target_points)

    def _step_time(self):
        self.current_simulation_timestamp += self.computation_timedelta
        self.current_simulation_timestamp_et = spice.str2et(self.current_simulation_timestamp.utc.iso)
        self.current_simulation_step += 1
        self.sweep_iterator.step(self.current_simulation_timestamp)

    def _set_time(self, time: Time, timestep: Optional[int] = None):
        self.current_simulation_timestamp = time
        self.current_simulation_timestamp_et = spice.str2et(time.utc.iso)
        self.current_simulation_step = 0 if timestep is None else timestep
        self.sweep_iterator.step(self.current_simulation_timestamp)

    def compute_distances_from_projected_vector(self, points, boresight):
        """
        Compute distances from the instrument's boresight to given points.
        """
        return np.linalg.norm(points - boresight, axis=1)

    def find_nearby_pits(self, instrument):
        """
        Uses the KD-Tree to find pits within the instrument's rough detection threshold.

        Returns:
        - nearby_points: Points within range
        - nearby_ids: Corresponding indices
        - boresight: Current instrument boresight position
        """
        intersection = instrument.compute_views_instrument_boresight(self.current_simulation_timestamp_et)
        boresight = intersection["boresight"]
        nearby_indices = self.kd_tree.query_ball_point(boresight, instrument.rough_treshold)
        return self._target_points[nearby_indices], self._target_ids[nearby_indices], boresight

    def adjust_timestep(self, boresights):
        min_distance = min(self.kd_tree.query(boresight)[0] for boresight in boresights)
        distance_discount = max([instrument.rough_treshold for instrument in self.instruments])
        new_time_step = (min_distance - distance_discount) / LRO_SPEED
        self.computation_timedelta = TimeDelta(min(max(TIME_STEP, new_time_step), MAX_TIME_STEP), format="sec")
        self.adjusted_timesteps.append(new_time_step)
        self.min_distances.append(min_distance)

    def run_simulation(self, max_steps: Optional[int] = None):
        # Prepare misc
        total_seconds = (self.max_time - self.min_time).to_value("sec")
        pbar_format_string = ("" if max_steps is None else f"/{max_steps}")

        # Here we store our points of interest to dump them into DB, eventually
        points_of_interest_batch = []

        # Run the main simulation loop
        with tqdm(total=total_seconds, ncols=TQDM_NCOLS, desc="Running simulation") as pbar:

            while self.current_simulation_timestamp <= self.max_time:
            
                # TQDM instrumentation
                pbar.update(self.computation_timedelta.to_value("sec"))
                if self.current_simulation_step % 256 == 0:
                    step_info = f"Simulation step:{self.current_simulation_step}"
                    failed_found_info = f"; failed: {len(self._failed_timestamps)}; found: {len(self._found_timestamps)}"
                    pbar.set_description(step_info + pbar_format_string + failed_found_info)

                # Check if we reached the maximum number of steps
                if max_steps is not None and self.current_simulation_step >= max_steps:
                    break

                try:
                    # Perform the simulation step
                    self._step_time()

                    # Compute projection of boresight for each instrument
                    for instrument in self.instruments:
                        # Projects to the lunar surface and looks for closest points (may be empty)
                        feasible_points, _, boresight = self.find_nearby_pits(instrument)
                        new_distances = self.compute_distances_from_projected_vector(feasible_points, boresight)
                        
                        
                        if any(new_distances < instrument.rough_treshold):
                            self._found_timestamps.append((boresight, self.current_simulation_timestamp, self.current_simulation_step))
                            self._found_timestamps_cnt += 1
                            #logging.info("Found!")
                    self.adjust_timestep(boresights)
                except Exception as e:
                    # logger.exception(
                    #     f"Error at step {self.current_simulation_step}: {e}"
                    # )
                    self._failed_timestamps.append((self.current_simulation_timestamp, self.current_simulation_step))
                    self._failed_timestamps_cnt += 1
        return
