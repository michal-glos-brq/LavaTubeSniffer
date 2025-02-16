import os
from astropy.time import Time
from dataclasses import dataclass
from typing import Optional
from tqdm import tqdm

import logging

import spiceypy

import sys
sys.path.insert(0, '/'.join(__file__.split("/")[:-4]))
from src.scripts.SPICE.config import DESTINATION, MAX_LOADED_SPICE

logger = logging.getLogger(__name__)

BASE_LBL_KEYS = {
    "filename_key": "^SPICE_KERNEL",
    "time_start_key": "START_TIME",
    "time_stop_key": "STOP_TIME",
}


@dataclass
class SPICEFile:
    filename: str
    time_start: Time
    time_stop: Time


class DynamicKernelLoader:
    """
    This class implements kernels fragmented in time. Implements loading correct kernels for required time
    """

    @property
    def min_loaded_time(self):
        """Min time in .lbl files for given KERNELs"""
        return self.kernel_pool[0].time_start

    @property
    def max_loaded_time(self):
        """Max time in .lbl files for given KERNELs"""
        return self.kernel_pool[-1].time_stop

    def __init__(self, kernels_id: str, resource: str, startswith: Optional[str] = None, filename_key: str = "^SPICE_KERNEL", time_start_key: str = "START_TIME", time_stop_key: str = "STOP_TIME"):
        self.name = kernels_id
        # Always assume the last is currently loaded kernel
        self.loaded_kernels = []
        self.kernel_pool = self.load_SPICE_metadata(resource, startswith, filename_key, time_start_key, time_stop_key)

    def refresh_SPICE_for_given_time(self, time: Time):
        """
        Return False when no SPICE available for given time
        
        Makes sure all SPICE kernels are loaded for given time
        """
        if self.loaded_kernels and self.loaded_kernels[-1].time_start <= time <= self.loaded_kernels[-1].time_stop:
            return True
        logger.debug(f"Loading SPICE for {self.name} at {time}")
        for kernel in self.kernel_pool:
            if kernel.time_start <= time <= kernel.time_stop:
                logger.debug(f"Loading SPICE {kernel.filename}")
                spiceypy.furnsh(kernel.filename)
                logger.debug(f"Loaded SPICE {kernel.filename}")
                self.loaded_kernels.append(kernel)
                if len(self.loaded_kernels) > MAX_LOADED_SPICE:
                    spiceypy.unload(self.loaded_kernels[0].filename)
                    self.loaded_kernels.pop(0)
                return True
        logger.debug(f"No SPICE available for {self.name} at {time}")
        return False

    def load_SPICE_metadata(
        self, resource: str, startswith: Optional[str], filename_key: str, time_start_key: str, time_stop_key: str
    ):
        """
        Loads metadata of SPICE kernels, so they could be loaded. Loads also timeframes for
        kernels in 
        """
        folder_name = os.path.join(DESTINATION, resource)
        files = os.listdir(folder_name)
        files = [
            file for file in files if file.endswith(".lbl") and (startswith is None or file.startswith(startswith))
        ]

        spice_series = []

        for file in tqdm(files, desc=f"Processing {resource}", ncols=200):
            with open(os.path.join(folder_name, file)) as f:
                spice = {}
                for line in f.readlines():
                    split_line = line.split("=")
                    if len(split_line) != 2:
                        continue
                    key, value = split_line
                    key = key.strip()
                    value = value.strip()
                    if key in [filename_key, time_start_key, time_stop_key]:
                        spice[key] = value
                if len(spice) != 3:
                    print(f"Skipping {file}, not sufficient data found")
                    continue
                try:
                    spice_series.append(
                        SPICEFile(
                            filename=os.path.join(DESTINATION, resource, spice[filename_key].replace('"', "")),
                            time_start=Time(spice[time_start_key], format="isot", scale="utc"),
                            time_stop=Time(spice[time_stop_key], format="isot", scale="utc"),
                        )
                    )
                except Exception as e:
                    print(f"Skipping {file}, invalid datetime format")
                    print(e)

        return sorted(spice_series, key=lambda x: x.time_start)
