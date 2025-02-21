"""
This script will parse the existing Lunar Pit MongoDB database and create a new parsed MongoDB database

Requires to run mongo.scrape-lunar-pits-database.py to scrape the dataset first
"""

import sys

from pymongo import MongoClient, GEOSPHERE
from tqdm import tqdm

from src.config.mongo_config import (
    MONGO_URI,
    PIT_ATLAS_DB_NAME,
    PIT_ATLAS_PARSED_DB_NAME,
    IMAGE_COLLECTION_NAME,
    PIT_DETAIL_COLLECTION_NAME,
    PIT_COLLECTION_NAME,
)
from src.db.mongo.models.lunar_pit_atlas import ImageCollection, PitDetailsCollection, PitsCollection


def perform_largescale_conversion_with_pydantic(collection_in, collection_out, model_class):
    """
    Perform large-scale transformation using Pydantic models for validation and conversion.
    """
    pbar = tqdm(
        total=collection_in.count_documents({}),
        desc=f"Processing {collection_in.name}",
        dynamic_ncols=True,
        leave=True,
        file=sys.stderr,
    )
    for doc in collection_in.find({}):
        try:
            # Validate and transform using Pydantic
            transformed_doc = model_class(**doc).dict(by_alias=True)
            # Exclude `_id` from the update
            update_fields = {k: v for k, v in transformed_doc.items() if k != "_id"}
        except Exception as e:
            print(f"Error processing document {doc['_id']}: {e}")
            continue  # Skip to the next document on error

        # Update the document in the target collection
        collection_out.update_one(
            {"_id": doc["_id"]},  # Match by unique ID
            {"$set": update_fields},
            upsert=True,  # Ensures the document is inserted if not already present
        )
        pbar.update(1)
    pbar.close()


def parse_lunar_pits_db():
    client = MongoClient(MONGO_URI)
    db_in = client.get_database(PIT_ATLAS_DB_NAME)
    db_out = client.get_database(PIT_ATLAS_PARSED_DB_NAME)

    # Process image collection
    collection_in = db_in[IMAGE_COLLECTION_NAME]
    if IMAGE_COLLECTION_NAME in db_out.list_collection_names():
        db_out.drop_collection(IMAGE_COLLECTION_NAME)
    collection_out = db_out.create_collection(IMAGE_COLLECTION_NAME)

    perform_largescale_conversion_with_pydantic(collection_in, collection_out, ImageCollection)

    # Process pit details collection
    collection_in = db_in[PIT_DETAIL_COLLECTION_NAME]
    if PIT_DETAIL_COLLECTION_NAME in db_out.list_collection_names():
        db_out.drop_collection(PIT_DETAIL_COLLECTION_NAME)
    collection_out = db_out.create_collection(PIT_DETAIL_COLLECTION_NAME)
    collection_out.create_index([("location", GEOSPHERE)])
    # Create index on name field
    collection_out.create_index([("name", 1)])

    perform_largescale_conversion_with_pydantic(collection_in, collection_out, PitDetailsCollection)

    # Process pits collection
    collection_in = db_in[PIT_COLLECTION_NAME]
    if PIT_COLLECTION_NAME in db_out.list_collection_names():
        db_out.drop_collection(PIT_COLLECTION_NAME)
    collection_out = db_out.create_collection(PIT_COLLECTION_NAME)
    collection_out.create_index([("location", GEOSPHERE)])
    # Create index on name field
    collection_out.create_index([("name", 1)])

    perform_largescale_conversion_with_pydantic(collection_in, collection_out, PitsCollection)


if __name__ == "__main__":
    parse_lunar_pits_db()
