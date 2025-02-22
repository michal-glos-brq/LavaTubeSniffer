from typing import List
import pandas as pd
from pymongo import MongoClient, errors
from src.config.mongo_config import (
    MONGO_URI,
    PIT_ATLAS_PARSED_DB_NAME,
    PIT_COLLECTION_NAME,
    SIMULATION_DB_NAME,
    SIMULATION_POINTS_COLLECTION,
)


class Sessions:
    """
    MongoDB session manager for simulation and pit location data.

    This class provides methods to:
      - Retrieve lunar pit locations as a Pandas DataFrame.
      - Insert simulation result documents into a MongoDB timeseries collection synchronously.

    Simulation results are stored in a timeseries collection with indexes on:
      - astro_timestamp (ephemeris time, ET, as a float)
      - instrument (instrument name)
      - min_distance (the computed minimum distance)
    """
    client: MongoClient = None
    sessions = {}
    lunar_pit_locations = None

    @staticmethod
    def get_db_session(db_name: str):
        """
        Returns a MongoDB database session for the given database name.
        If the session does not already exist, it is created.
        If the database is new, a temporary collection is created and dropped.
        """
        if Sessions.client is None:
            Sessions.client = MongoClient(MONGO_URI)

        if hasattr(Sessions.sessions, db_name):
            return Sessions.sessions[db_name]

        if db_name not in Sessions.client.list_database_names():
            Sessions.client[db_name].create_collection("placeholder_collection")
            Sessions.client[db_name]["placeholder_collection"].drop()
        Sessions.sessions[db_name] = Sessions.client[db_name]
        return Sessions.sessions[db_name]

    @staticmethod
    def get_all_pits_points():
        """
        Fetches all lunar pit locations from the MongoDB collection and returns them as a Pandas DataFrame.

        The resulting DataFrame uses the pit 'name' as its index and includes 'latitude' and 'longitude' columns.
        """
        if Sessions.lunar_pit_locations is not None:
            return Sessions.lunar_pit_locations

        session = Sessions.get_db_session(PIT_ATLAS_PARSED_DB_NAME)
        collection = session[PIT_COLLECTION_NAME]
        query_results = list(collection.find({}, {"location": 1, "name": 1}))
        data = [
            {
                "name": item["name"],
                "latitude": item["location"]["coordinates"][1],
                "longitude": item["location"]["coordinates"][0]
            }
            for item in query_results
        ]
        Sessions.lunar_pit_locations = pd.DataFrame(data)
        Sessions.lunar_pit_locations.set_index("name", inplace=True)
        return Sessions.lunar_pit_locations

    @staticmethod
    def _prepare_simulation_collection():
        """
        Ensures that the simulation results collection exists.
        - Stores `et` as a float (ephemeris time) instead of BSON datetime.
        - Keeps `instrument` as a direct field.
        - Stores `sub_instrument` inside the `meta` dictionary.
        """
        session = Sessions.get_db_session(SIMULATION_DB_NAME)
        if SIMULATION_POINTS_COLLECTION not in session.list_collection_names():
            try:
                session.create_collection(SIMULATION_POINTS_COLLECTION)  # Regular collection, not time-series
            except errors.CollectionInvalid:
                pass  # Collection already exists
        collection = session[SIMULATION_POINTS_COLLECTION]

        # Indexes for efficient queries
        collection.create_index("instrument")  # Faster instrument filtering
        collection.create_index("et")  # Index for ephemeris time queries
        collection.create_index("min_distance")  # Index for proximity queries
        return collection

    @staticmethod
    def insert_simulation_results(results: List[dict]):
        """
        Inserts a batch of simulation result documents into MongoDB.

        **Expected Format:**
        ```json
        [
            {
                "instrument": "<instrument_name>",
                "et": <float>,  # Ephemeris time as float
                "min_distance": <float>,  # Distance metric
                "meta": {
                    "sub_instrument": "<sub_instrument_id (optional)>"
                }
            }
        ]
        ```
        
        - `et`: Stored as a float (not BSON datetime).
        - `meta.sub_instrument`: Optional field inside the `meta` dictionary.
        """
        collection = Sessions._prepare_simulation_collection()
        if results:
            for result in results:
                # Ensure the required fields exist
                result.setdefault("meta", {})  # Ensure meta exists
                result["meta"].setdefault("sub_instrument", None)  # Default sub_instrument to None if missing
            
            collection.insert_many(results)
