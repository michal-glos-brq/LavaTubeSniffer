from requests import Response
from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.dataset.datasets.base_dataset import AbstractDatasetLRO


class WacGLOBAL(AbstractDatasetLRO):

    BASE_URL = "https://pds.lroc.asu.edu/data/"
    REMOTE_DIR = "LRO-L-LROC-5-RDR-V1.0/"
    DOWNLOAD_DIR = "/media/mglos/HDD1_8TB1/GLOBAL/NarrowAngleCameraLRC"

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
