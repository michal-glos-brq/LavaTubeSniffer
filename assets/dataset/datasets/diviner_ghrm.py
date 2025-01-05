import asyncio
from requests import Response
from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.dataset.datasets.base_dataset import AbstractDatasetLRO


# GHRM provides gridded high resolution data of the lunar surface
# LVL2 data would provide calibrated a corrected data from 9 channels for more thorough analysis


class DivinerGHRM(AbstractDatasetLRO):

    BASE_URL = "https://pds-geosciences.wustl.edu/"
    REMOTE_DIR = "lro/urn-nasa-pds-lro_diviner_derived1/data_derived_ghrm/"
    DOWNLOAD_DIR = "/media/mglos/HDD1_8TB1/GLOBAL/DIVINER_GHRM"

    def __init__(self):
        super().__init__(self.BASE_URL, self.REMOTE_DIR, self.DOWNLOAD_DIR)

    def folder_file_interest(self, filename: str) -> bool:
        return filename.endswith(("img", "tif", "tiff", "xml", "csv"))

    def parse_file_page(self, response: Response) -> Dict[str, List[tuple[str, str]]]:
        """Use Beautiful soup to parse out links to folders and files"""
        files, folders = [], []
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a"):
            href = urljoin(self.dataset_root_url, link.get("href"))
            text = link.text.strip().split("/")[-1]
            if href.endswith("/"):
                folders.append((href, text))
            else:
                files.append((href, text))
        return {"files": files, "folders": folders}
