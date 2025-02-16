import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, List, Union, Dict

import numpy as np
import spiceypy as spice
import logging
import sys



logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)



sys.path.insert(0, "/".join(__file__.split("/")[:-4]))
from src.scripts.SPICE.config import (
    DIVINER_INSTRUMENT_IDS,
    LRO_DIVINER_FRAME_STR_ID,
    MOON_STR_ID,
    LRO_STR_ID,
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

    @dataclass
    class ProjectedPoint:
        instrument_id: int
        et: float
        # Points are 3D
        boresight: Union[Tuple[float, float, float], None]
        boresight_trgepc: Union[float, None]
        bounds: Tuple[
            Union[np.array, None],
            Union[np.array, None],
            Union[np.array, None],
            Union[np.array, None],
        ]
        bounds_trgepc: Union[List[float], None] # Of len 4 ...


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

    sub_instruments = None

    def __init__(self):
        self.sub_instruments = {}
        for naif_id in self.instrument_ids:
            # Get FOV shape, boresight, and boundary vectors
            _, frame, boresight, _, bounds = spice.getfov(naif_id, room=1000)
            self.sub_instruments[naif_id] = self.SubInstrument(naif_id, frame, np.array(bounds), np.array(boresight))

    def compute_rays(self, et) -> Dict[int, ProjectedPoint]:
        """
        Compute rays for the instrument at given time
        Will project the point in 
        """
        rays = {}
        for sub_instrument in self.sub_instruments.values():
            boresight_point, boresight_trgepc, _ = spice.sincpt(
                    "DSK/UNPRIORITIZED",
                    MOON_STR_ID,
                    et,  # Time (just a number, the astro time)
                    MOON_REF_FRAME_STR_ID,
                    ABBERRATION_CORRECTION,
                    self.satellite_frame,
                    self.frame,
                    spice.mxv(spice.pxform(sub_instrument.frame, self.frame, et), sub_instrument.boresight)
            )
            bound_points, bound_trgpecs = [], []
            for bound in sub_instrument.bounds:
                bound_point, bound_trgpec, _ = spice.sincpt(
                    "DSK/UNPRIORITIZED",
                    MOON_STR_ID,
                    et,  # Time (just a number, the astro time)
                    MOON_REF_FRAME_STR_ID,
                    ABBERRATION_CORRECTION,
                    self.satellite_frame,
                    self.frame,
                    spice.mxv(spice.pxform(sub_instrument.frame, self.frame, et), bound)
                )
                bound_points.append(bound_point)
                bound_trgpecs.append(bound_trgpec)
                
            rays[sub_instrument._id] = self.ProjectedPoint(
                instrument_id=sub_instrument._id,
                et=et,
                boresight=boresight_point,
                boresight_trgepc=boresight_trgepc,
                bounds=bound_points,
                bounds_trgepc=bound_trgpecs
            )
        return rays


class DIVINERInstrument(Instrument):
    name = "DIVINER"
    instrument_ids = DIVINER_INSTRUMENT_IDS
    frame = LRO_DIVINER_FRAME_STR_ID
    satellite_frame = LRO_STR_ID
    offset_days = 6.3552