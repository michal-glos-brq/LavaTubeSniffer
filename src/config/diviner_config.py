"""
This file contains configuration for the Diviner dataset processing.
"""

# Remote dataset location
DIVINER_BASE_URL = "https://pds-geosciences.wustl.edu"
BASE_SUFFIX = "/lro/lro-l-dlre-4-rdr-v1/"

# This are the BASE URLs we consider as roots for the webcrawler
# BASE_URLS = ["https://pds-geosciences.wustl.edu/lro/lro-l-dlre-4-rdr-v1/lrodlr_1002/data/2023/202307/20230701/"]
BASE_URLS = ["https://pds-geosciences.wustl.edu/lro/lro-l-dlre-4-rdr-v1/lrodlr_1002/data/2023/"]

# File suffixes we care to download
FILE_SUFFIXES = {".zip", ".xml"}

# We are interested in data in 5 Km radius around the lunar pits
RADIUS_KM = 5
