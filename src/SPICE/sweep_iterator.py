"""
This script goes through the SPICE data and finds time
intervals LRO DIVINER is within area of interests
"""

import os
import logging
import sys

sys.path.insert(0, "/".join(__file__.split("/")[:-3]))
from astropy.time import Time
import spiceypy as spice
from tqdm import tqdm

from src.global_config import TQDM_NCOLS
from src.SPICE.config import (
    DESTINATION,
    LONE_KERNELS,
    LUNAR_MODEL,
)
from src.db.mongo.interface import Sessions
from src.SPICE.kernels.dynamic_kernel_loader import DynamicKernelLoader

from src.global_config import TQDM_NCOLS

logger = logging.getLogger(__name__)

points = Sessions.get_all_pits_points()


class SweepIterator:
    """
    This SweepIterator ensures we have correct SPICE files loaded for given datetime
    """

    @property
    def min_loaded_time(self) -> Time:
        return max([kernel.min_loaded_time for kernel in self.dynamic_kernels])

    @property
    def max_loaded_time(self) -> Time:
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
            file_path = os.path.join(DESTINATION, folder) if folder is not None else DESTINATION
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

        for kernel in tqdm(kernels, ncols=TQDM_NCOLS, desc="Loading static SPICE kernels from folders"):
            spice.furnsh(kernel)

        for kernel in tqdm(LONE_KERNELS, ncols=TQDM_NCOLS, desc="Loading lone SPICE kernels from files"):
            spice.furnsh(kernel["path"])

        logging.info("Loading detailed model of the Moon")
        spice.furnsh(LUNAR_MODEL["dsk_path"])

    def step(self, time: Time):
        return all([kernel.refresh_SPICE_for_given_time(time) for kernel in self.dynamic_kernels])

    def initiate_sweep(self, starting_datetime: Time) -> None:
        if not self.step(starting_datetime):
            raise ValueError("Some of dynamic SPICE kernels were not loaded for required time")
