"""
This file provides interface for mongoDB
"""

from pymongo import MongoClient

from src.config.mongo_config import MONGO_URI, DB_NAME, DB_NAME_PARSED, PIT_COLLECTION_NAME

def get_all_pits_points(session):
    collection = session[PIT_COLLECTION_NAME]
    return list(collection.find({}, {"location": 1, "name": 1}))


def get_db_session(parsed=True):
    db_name = DB_NAME_PARSED if parsed else DB_NAME
    client = MongoClient(MONGO_URI)

    if db_name not in client.list_database_names():
        client[db_name].create_collection("placeholder_collection")
        client[db_name]["placeholder_collection"].drop()
    return client[db_name]
