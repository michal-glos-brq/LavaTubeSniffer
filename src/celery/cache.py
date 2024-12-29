"""
This server as module level cache
"""
import logging
from src.mongo.interface import get_db_session, get_all_pits_points


logger = logging.getLogger(__name__)

lunar_pit_locations = []

def get_lunar_pit_locations():
    global lunar_pit_locations
    if lunar_pit_locations:
        return lunar_pit_locations
    else:
        logger.info("Fetching all lunar pit locations")
        lunar_pit_locations = get_all_pits_points(get_db_session())
        return lunar_pit_locations

        
