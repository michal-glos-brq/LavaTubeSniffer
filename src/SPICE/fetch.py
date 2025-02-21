"""
This script downloads SPICE data from NAIF JPL and other sources
"""

import os
import requests
import argparse
from tqdm import tqdm
import logging

from bs4 import BeautifulSoup as bs

import sys

sys.path.insert(0, "/".join(__file__.split("/")[:-3]))
from src.SPICE.config import BASE_URL, DESTINATION, LONE_KERNELS, LUNAR_MODEL, lro_resources
from src.SPICE.kernels.dsk_utils import xyz_to_dsk_model


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],  # Force output to stdout
)
logger = logging.getLogger()


parser = argparse.ArgumentParser(description="Download SPICE data from NAIF JPL")
parser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite existing files")
parser.add_argument("--tif", action="store_true", help="Force generation of Lunar model from TIF")


args = parser.parse_args()

# OVERWRITE_EXISTING = False
OVERWRITE_EXISTING = args.overwrite
OVERWRITE_LUNAR_MODEL = args.tif
MAX_RETRIES = 5


def download_file(file_url, file_destination, show_pbar=False):
    """
    Simple universal function to download a remote file to a local destination
    """
    with requests.get(file_url, stream=True) as r:
        r.raise_for_status()
        with open(file_destination, "wb") as f:
            if show_pbar:
                total_size = int(r.headers.get("content-length", 0))
                file_iterator = tqdm(r.iter_content(chunk_size=8192), total=total_size, unit="B", unit_scale=True)
            else:
                file_iterator = r.iter_content(chunk_size=8192)
            for chunk in file_iterator:
                f.write(chunk)


def main():
    # Here we hold the failed downloads to retry them in the future
    failed_files = {}

    logger.info("Fetching SPICE data from NAIF JPL")

    # Download SPICE kernels directly related to the LRO mission
    # List the parent folders and fetch all the files matching the regex
    for resource in lro_resources:
        os.makedirs(os.path.join(DESTINATION, resource), exist_ok=True)
        response = requests.get(f"{BASE_URL}{resource}/")
        soup = bs(response.text, "html.parser")

        links = soup.find_all("a")
        links = [link for link in links if lro_resources[resource].match(link.get("href") or "")]
        for link in tqdm(links, ncols=100, desc=f"{resource}"):
            filename = link.get("href")
            file_url = f"{BASE_URL}{resource}/{filename}"
            file_destination = os.path.join(DESTINATION, resource, filename)

            if os.path.exists(file_destination) and not OVERWRITE_EXISTING:
                continue

            try:
                download_file(file_url, file_destination)
            except:
                failed_files[filename] = (file_url, file_destination)

    # Download lone kernels without listing the parent folders
    logger.info(f"Fetching {len(LONE_KERNELS)} lone kernels")
    for lone_kernel in LONE_KERNELS:
        file_url = lone_kernel["url"]
        file_destination = lone_kernel["path"]

        if os.path.exists(file_destination) and not OVERWRITE_EXISTING:
            logging.info(f"{file_destination} already exists")
            continue

        try:
            logger.info(f"Downloading {file_destination}")
            download_file(file_url, file_destination, show_pbar=True)
        except:
            failed_files[os.path.basename(file_destination)] = (file_url, file_destination)

    # Download elevation model and parse it into dsk format for SPICE
    # This is a bit more complicated and requires GDAL (sudo apt install gdal-bin)
    logger.info("Fetching DSK model")

    # Check for TIF file, eventually download it
    if not os.path.exists(LUNAR_MODEL["tif_path"]) or OVERWRITE_LUNAR_MODEL:
        try:
            download_file(LUNAR_MODEL["url"], LUNAR_MODEL["tif_path"], show_pbar=True)
        except:
            failed_files[os.path.basename(LUNAR_MODEL["tif_path"])] = (LUNAR_MODEL["url"], LUNAR_MODEL["tif_path"])
    else:
        logger.info("Lunar TIF model already exists")

    # Check for XYZ, eventually convert it with GDAL
    if not os.path.exists(LUNAR_MODEL["xyz_path"]) or OVERWRITE_LUNAR_MODEL:
        if not os.path.exists(LUNAR_MODEL["tif_path"]):
            logger.error("Lunar TIF model not found, will not create the DSK model")
        else:
            for command in LUNAR_MODEL["commands"]:
                process = os.system(command)
                if process != 0:
                    logger.error(f"Failed to execute command: {command}")
                    break
        logger.info("Commands executed successfully")

    # Check for DSK model, eventually convert it with out custom function
    if not os.path.exists(LUNAR_MODEL["dsk_path"]) or OVERWRITE_LUNAR_MODEL:
        if not os.path.exists(LUNAR_MODEL["xyz_path"]):
            logger.error("Lunar XYZ model not found, will not create the DSK model")
        else:
            xyz_to_dsk_model()
            logger.info("DSK model created successfully")
    else:
        logger.info("Lunar DSK model already exists")

    if os.path.exists(LUNAR_MODEL["dsk_path"]) and not OVERWRITE_EXISTING:
        logger.info("Lunar DSK model already exists")
    elif os.path.exists(LUNAR_MODEL["xyz_path"]) and not OVERWRITE_EXISTING:
        logger.info("Lunar XYZ model already exists, ")

    # In case an error occured while downloading, try to download failed files again
    if failed_files:
        logger.info("Retrying failed downloads")
    for i in range(MAX_RETRIES):
        if failed_files:
            _failed_files = {
                filename: (file_url, file_destination)
                for filename, (file_url, file_destination) in failed_files.items()
            }
            failed_files = {}
            for filename, (file_url, file_destination) in tqdm(
                _failed_files.items(), ncols=100, desc=f"Retrying No.{i+1}"
            ):
                try:
                    download_file(file_url, file_destination)
                except:
                    failed_files[filename] = (file_url, file_destination)
        else:
            break

    return failed_files


if __name__ == "__main__":
    failed_files = main()
    if not failed_files:
        logger.info("Download completed successfully")
    else:
        logger.info("Failed to download:" + "\n" + "\n".join(failed_files.keys()))
