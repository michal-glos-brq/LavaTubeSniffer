"""
This is basically a webcrawler, crawling diviner dataset servers, creating tasks for celery workers with
the intent to extract data from the diviner dataset servers from specific locations.
"""

import re
from requests import Response
from typing import List
from urllib.parse import urljoin
from collections import defaultdict
import logging

from bs4 import BeautifulSoup

from src.celery.initiators.base_initiator import BaseInitiator
from src.config.diviner_config import RADIUS_KM, BASE_URLS, DIVINER_BASE_URL
from src.celery.app import diviner_task


class DivinerInitiator(BaseInitiator):
    """
    This class is used to initiate the diviner dataset sweep.
    """

    DATASET_NAME = "Diviner"
    BASE_URLS = BASE_URLS
    filename_regex = re.compile(r"20[0-4][0-9]")
    suffix_regex = re.compile(r".zip|.xml")
    reject_regex = re.compile(r".lbl")

    def __init__(self):
        super().__init__(RADIUS_KM)

    def parse_file_page(self, response: Response) -> List[str]:
        """
        This function is used to parse the file page.
        """
        folders, files = [], []
        soup = BeautifulSoup(response.text, "html.parser")
        for link in soup.find_all("a"):
            href = urljoin(DIVINER_BASE_URL, link.get("href"))

            # Get rid of parent folder and weird loops
            if href in response.url:
                continue

            filename = href.split("/")[-1]
            if re.search(self.reject_regex, filename):
                continue
            elif re.search(self.suffix_regex, filename):
                files.append(href)
            elif re.search(self.filename_regex, filename):
                folders.append(href)
        return folders, files

    def create_celery_tasks(self, urls: List[str]) -> List[str]:
        """
        This function is used to create celery tasks.
        """
        data_base_urls = defaultdict(dict)
        for url in urls:
            url_split = url.split(".")
            base_url = ".".join(url_split[:-1])
            # Here we just put the suffixes as keys, because we have xml and datafile for each base url
            data_base_urls[base_url][url_split[-1]] = url

        assigned_urls = []
        for data in data_base_urls.values():
            if "xml" in data and "zip" in data:
                diviner_task.apply_async(args=(data["xml"], data["zip"], self.tolerance))
                logging.info(f"Initiated task for {data['xml']} and {data['zip']}")
                assigned_urls.extend([data["xml"], data["zip"]])
                break
            else:
                print("Something went wrong, you should probably check the data")

        return assigned_urls
