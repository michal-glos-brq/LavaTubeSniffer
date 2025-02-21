import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, List, Dict, Optional

import numpy as np
import spiceypy as spice
import logging
import sys


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


sys.path.insert(0, "/".join(__file__.split("/")[:-4]))
from src.SPICE.config import (
    MOON_STR_ID,
    ABBERRATION_CORRECTION,
    MOON_REF_FRAME_STR_ID,
)


class Instrument(ABC):

    @dataclass
    class SubInstrument:
        _id: int
        frame: str
        bounds: np.array
        boresight: np.array

    _boresight = None

    @property
    def boresight(self):
        if self._boresight is None:
            self._boresight = np.stack([sub.boresight for sub in self.sub_instruments.values()]).mean(axis=0)
        return self._boresight

    @property
    @abstractmethod
    def subinstrumen_offset(self) -> float: ...

    @property
    @abstractmethod
    def fov_offset(self) -> float: ...

    @property
    @abstractmethod
    def distance_tolerance(self) -> float: ...

    @property
    def rough_treshold(self) -> float:
        return self.subinstrumen_offset + self.distance_tolerance + self.fov_offset

    @property
    def finer_treshold(self) -> float:
        return self.distance_tolerance

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def instrument_ids(self) -> str: ...

    @property
    @abstractmethod
    def satellite_frame(self) -> str: ...

    @property
    @abstractmethod
    def offset_days(self) -> float: ...

    @property
    def sub_instrument_frames(self) -> List[str]:
        return [sub_instrument.frame for sub_instrument in self.sub_instruments.values()]

    def transformation_matrix(self, et) -> Optional[np.array]:
        if et == self._transformation_matrix[0]:
            return self._transformation_matrix[1]
        else:
            matrix = spice.pxform(self.uniform_sub_instrument_frame, self.frame, et)
            self._transformation_matrix = (et, matrix)
            return matrix

    def __init__(self):
        self.sub_instruments: Dict[int, Tuple[str, np.ndarray, np.ndarray]] = {}
        for naif_id in self.instrument_ids:
            # Get FOV shape, boresight, and boundary vectors
            _, frame, boresight, _, bounds = spice.getfov(naif_id, room=1000)
            self.sub_instruments[naif_id] = self.SubInstrument(naif_id, frame, np.array(bounds), np.array(boresight))

        # Setting the uniform frame for all sub-instruments to skip on tranformation matrix computation for each subinstrument
        if len(set(self.sub_instrument_frames)) == 1:
            self.uniform_sub_instrument_frame = self.sub_instrument_frames[0]
            self._transformation_matrix = (-1, None)
        else:
            raise NotImplementedError("Different subinstrument frames are not supported yet")
            self.uniform_sub_instrument_frame = None

    def project_vector(self, et, vector) -> np.array:
        return spice.sincpt(
            "DSK/UNPRIORITIZED",
            MOON_STR_ID,
            et,  # Time (just a number, the astro time)
            MOON_REF_FRAME_STR_ID,
            ABBERRATION_CORRECTION,
            self.satellite_frame,
            self.frame,
            vector,
        )

    def compute_views_instrument_boresight(self, et) -> Dict[str, Dict]:
        """
        Compute views for the instrument at given time
        Where on the Lunar surface are we looking at
        """
        boresight_point, boresight_trgepc, _ = self.project_vector(
            et, spice.mxv(self.transformation_matrix(et), self.boresight)
        )
        return {"et": et, "boresight": boresight_point, "boresight_trgepc": boresight_trgepc}

    def compute_views_subinstruments_boresight(self, et) -> Dict[int, Dict]:
        """
        Compute views for the instrument at given time
        Will project the point in
        """
        # Here, we store ProjectedPoint for each subinstrument
        boresights = {}

        for sub_instrument in self.sub_instruments.values():
            boresight_point, boresight_trgepc, _ = self.project_vector(
                et, spice.mxv(self.transformation_matrix(et), sub_instrument.boresight)
            )
            boresights[sub_instrument._id] = {
                "et": et,
                "boresight": boresight_point,
                "boresight_trgepc": boresight_trgepc,
            }
        return boresights

    def compute_views_subinstruments_bounds(self, et) -> Dict[int, Dict]:
        """
        Compute views for the instrument at given time
        Will project the point in
        """
        # Here, we store ProjectedPoint for each subinstrument
        bounds = {}

        for sub_instrument in self.sub_instruments.values():
            bound_points, bound_trgpecs = [], []
            for bound in sub_instrument.bounds:
                bound_point, bound_trgpec, _ = self.project_vector(et, spice.mxv(self.transformation_matrix(et), bound))
                bound_points.append(bound_point)
                bound_trgpecs.append(bound_trgpec)
            bounds[sub_instrument._id] = {
                "et": et,
                "bounds": bound_points,
                "bounds_trgepc": bound_trgpecs,
            }
        return bounds
