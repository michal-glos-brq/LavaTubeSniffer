"""
This file serves as a central configuration file for the MongoDB related code, saved in src/mongo
"""

## Local
IMG_BASE_FOLDER = "/media/mglos/HDD1_8TB1/MONGO/PITS_IMAGES"

## Mongo
MONGO_URI = "mongodb://admin:password@localhost:27017"
DB_NAME = "lro_pits"
DB_NAME_PARSED = "lro_pits_parsed"

IMAGE_COLLECTION_NAME = "images"
PIT_COLLECTION_NAME = "pits"
PIT_DETAIL_COLLECTION_NAME = "pit_details"
COLECTIONS = [PIT_COLLECTION_NAME, PIT_DETAIL_COLLECTION_NAME, IMAGE_COLLECTION_NAME]

MONGO_HEADERS = [
    "hosting_feature",
    "name",
    "latitude",
    "longitude",
    "funnel_max_diameter",
    "funnel_min_diameter",
    "inner_max_diameter",
    "inner_max_diameter_sorting",
    "inner_min_diameter",
    "inner_min_diameter_sorting",
    "azimuth",
    "depth",
    "depth_sorting",
    "link_suffix",
]


# LRO server
LIST_URL = "https://www.lroc.asu.edu/atlases/pits/list"
BASE_URL = "https://www.lroc.asu.edu/"

# Maximal wait time will be sleep_time * 2 ** MAX_RETRIES
MAX_RETRIES = 5 # sleep_time * 32, which is 8 minutes

# LRO data

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.170 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

EXPECTED_HEADERS = [
    "Host Feat.",
    "Name",
    "Lat.",
    "Long.",
    "Funnel Max Diam. (m)",
    "Funnel Min Diam. (m)",
    "Inner Max Diam. (m)",
    "Inner Max Diam. Sorting",
    "Inner Min Diam. (m)",
    "Inner Min Diam. Sorting",
    "Azimuth",
    "Depth (m)",
    "Depth Sorting",
]
