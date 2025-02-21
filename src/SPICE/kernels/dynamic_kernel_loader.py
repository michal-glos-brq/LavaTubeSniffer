import os
import logging
import spiceypy as spice
import re
from astropy.time import Time
from typing import Optional, List, NamedTuple
from tqdm import tqdm
import sys

sys.path.insert(0, "/".join(__file__.split("/")[:-3]))
from src.SPICE.config import DESTINATION, MAX_LOADED_SPICE
from src.global_config import TQDM_NCOLS

logger = logging.getLogger(__name__)


class SPICEFile(NamedTuple):
    filename: str
    time_start: Time
    time_stop: Time


class DynamicKernelLoader:
    @property
    def min_loaded_time(self) -> Time:
        return self.kernel_pool[0].time_start

    @property
    def max_loaded_time(self) -> Time:
        return self.kernel_pool[-1].time_stop

    def __init__(
        self,
        kernels_id: str,
        resource: str,
        startswith: Optional[str] = None,
        filename_key: str = "^SPICE_KERNEL",
        time_start_key: str = "START_TIME",
        time_stop_key: str = "STOP_TIME",
    ) -> None:
        self.name = kernels_id
        self.loaded_kernels: List[SPICEFile] = []
        self.active_kernel_id = -1
        self.kernel_pool = self.load_SPICE_metadata(resource, startswith, filename_key, time_start_key, time_stop_key)
        # self.remove_redundant_kernels()

    def refresh_SPICE_for_given_time(self, time: Time) -> bool:
        if self.loaded_kernels and self.loaded_kernels[-1].time_start <= time <= self.loaded_kernels[-1].time_stop:
            return True
        kernel_to_load: Optional[SPICEFile] = None
        if (
            self.kernel_pool[self.active_kernel_id + 1].time_start
            <= time
            <= self.kernel_pool[self.active_kernel_id + 1].time_stop
        ):
            self.active_kernel_id += 1
            kernel_to_load = self.kernel_pool[self.active_kernel_id]
        else:
            for i, kernel in enumerate(self.kernel_pool):
                if kernel.time_start <= time <= kernel.time_stop:
                    self.active_kernel_id = i
                    kernel_to_load = kernel
                    break
        if kernel_to_load:
            spice.furnsh(kernel_to_load.filename)
            self.loaded_kernels.append(kernel_to_load)
            if len(self.loaded_kernels) > MAX_LOADED_SPICE:
                spice.unload(self.loaded_kernels[0].filename)
                self.loaded_kernels.pop(0)
            return True
        else:
            logger.debug("No SPICE available for %s at %s", self.name, time)
            return False

    def load_SPICE_metadata(
        self, resource: str, startswith: Optional[str], filename_key: str, time_start_key: str, time_stop_key: str
    ) -> List[SPICEFile]:
        folder_name = os.path.join(DESTINATION, resource)
        files = [
            f
            for f in os.listdir(folder_name)
            if f.endswith(".lbl") and (startswith is None or f.startswith(startswith))
        ]
        spice_series: List[SPICEFile] = []
        pattern = re.compile(r"(\S+)\s*=\s*(.+)")
        for file in tqdm(files, desc=f"Processing {resource}", ncols=TQDM_NCOLS):
            try:
                with open(os.path.join(folder_name, file), "r") as f:
                    content = f.read()
                metadata = {m.group(1): m.group(2).strip('"') for m in pattern.finditer(content)}
                if not all(key in metadata for key in [filename_key, time_start_key, time_stop_key]):
                    logger.warning("Skipping %s, insufficient data", file)
                    continue
                spice_series.append(
                    SPICEFile(
                        filename=os.path.join(DESTINATION, resource, metadata[filename_key]),
                        time_start=Time(metadata[time_start_key], format="isot", scale="utc"),
                        time_stop=Time(metadata[time_stop_key], format="isot", scale="utc"),
                    )
                )
            except Exception as e:
                logger.error("Skipping %s, error parsing metadata: %s", file, e)
        return sorted(spice_series, key=lambda x: x.time_start)


