"""
This file serves as a central configuration file for the MongoDB related code, saved in src/mongo
"""

### Mongo Structure and stuff
MONGO_URI = "mongodb://admin:password@localhost:27017"

PIT_ATLAS_DB_NAME = "lro_pits"
PIT_ATLAS_PARSED_DB_NAME = "lro_pits_parsed"

IMAGE_COLLECTION_NAME = "images"
PIT_COLLECTION_NAME = "pits"
PIT_DETAIL_COLLECTION_NAME = "pit_details"

DIVINER_COLLECTION_NAME = "diviner"

INITIAL_DOWNLOAD_RESET_TIME_SECONDS = 15

### Configuration for local-ran scripts (Pit Atlas scraping and parsing)
IMG_BASE_FOLDER = "/media/mglos/HDD1_8TB1/MONGO/PITS_IMAGES"

PIT_ATLAS_LIST_URL = "https://www.lroc.asu.edu/atlases/pits/list"
PIT_ATLAS_BASE_URL = "https://www.lroc.asu.edu/"

EXPECTED_PIT_TABLE_COLUMNS = [
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

PIT_TABLE_COLUMNS = [
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
# Maximal wait time will be sleep_time * 2 ** MAX_RETRIES
REQUEST_MAX_RETRIES = 5  # sleep_time * 32, which is 8 minutes

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.170 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}



### Simulation data
SIMULATION_DB_NAME = "astro-simulation"
SIMULATION_POINTS_COLLECTION = "simulation_points"
