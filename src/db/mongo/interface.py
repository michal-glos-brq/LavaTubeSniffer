"""
This file provides interface for mongoDB
"""
import pandas as pd
from pymongo import MongoClient

from src.config.mongo_config import MONGO_URI, PIT_ATLAS_DB_NAME, PIT_ATLAS_PARSED_DB_NAME, PIT_COLLECTION_NAME

class Sessions:
    """
    DB session manager, not to open new sessions all the time, should statically store the sessions
    """
    client: MongoClient = None
    sessions: dict = {}
    lunar_pit_locations = None

    @staticmethod
    def get_db_session(parsed=True, db_name=None):
        if db_name is None:
            db_name = PIT_ATLAS_PARSED_DB_NAME if parsed else PIT_ATLAS_DB_NAME

        if Sessions.sessions.get(db_name):
            return Sessions.sessions[db_name]

        if Sessions.client is None:
            Sessions.client = MongoClient(MONGO_URI)

        if db_name not in Sessions.client.list_database_names():
            Sessions.client[db_name].create_collection("placeholder_collection")
            Sessions.client[db_name]["placeholder_collection"].drop()
        return Sessions.client[db_name]

    @staticmethod
    def get_all_pits_points():
        """
        Fetch all lunar pit locations from the MongoDB collection and convert to a DataFrame.

        Returns:
            pd.DataFrame: DataFrame with pit names as index and latitude/longitude as columns.
        """
        if Sessions.lunar_pit_locations is not None:
            return Sessions.lunar_pit_locations

        session = Sessions.get_db_session(parsed=True)
        collection = session[PIT_COLLECTION_NAME]
        # Query to fetch the 'location' and 'name' fields
        query_results = list(collection.find({}, {"location": 1, "name": 1}))

        # Convert query results to a DataFrame
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

