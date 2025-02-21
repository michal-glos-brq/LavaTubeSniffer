import sys
import logging

sys.path.insert(0, "/".join(__file__.split("/")[:-4]))
from src.SPICE.config import (
    DIVINER_INSTRUMENT_IDS,
    LRO_DIVINER_FRAME_STR_ID,
    LRO_STR_ID,
    QUERY_RADIUS_MULTIPLIER,
)
from src.SPICE.instruments.base_instrument import Instrument


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)



class DIVINERInstrument(Instrument):
    name = "DIVINER"
    instrument_ids = DIVINER_INSTRUMENT_IDS
    # Frame of the instrument
    frame = LRO_DIVINER_FRAME_STR_ID
    satellite_frame = LRO_STR_ID
    # Until succesfull Lunara projection
    offset_days = 6.3552
    # Distance on the Lunar surface between the middle of all suinstruments and furthest subinstrument (4.3 Km measured from low sample)
    subinstrumen_offset = 6
    # Distance of fov from pit treshold
    #distance_tolerance = 5 * QUERY_RADIUS_MULTIPLIER
    # Increase to 12 Kms
    distance_tolerance = 12 * QUERY_RADIUS_MULTIPLIER
    # Distance from projected boresight to bound
    fov_offset = 3
