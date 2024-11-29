from pymongo import MongoClient, GEOSPHERE
from tqdm import tqdm
from src.dataset.pits.config import (
    MONGO_URI,
    DB_NAME,
    DB_NAME_PARSED,
    IMAGE_COLLECTION_NAME,
    PIT_DETAIL_COLLECTION_NAME,
    PIT_COLLECTION_NAME,
)
from dataset.pits.models import ImageCollection, PitDetailsCollection, PitsCollection


def validate_and_transform(collection, model_class, doc):
    """
    Validate and transform a MongoDB document using a Pydantic model.
    """
    try:
        return model_class(**doc).dict(by_alias=True)
    except Exception as e:
        print(f"Validation failed for document {doc['_id']}: {e}")
        return None


def perform_largescale_conversion_with_pydantic(collection_in, collection_out, model_class):
    """
    Perform large-scale transformation using Pydantic models for validation and conversion.
    """
    pbar = tqdm(total=collection_in.count_documents({}), desc=f"Processing {collection_in.name}", ncols=100)
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


def main():
    client = MongoClient(MONGO_URI)
    db_in = client.get_database(DB_NAME)
    db_out = client.get_database(DB_NAME_PARSED)

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

    perform_largescale_conversion_with_pydantic(collection_in, collection_out, PitDetailsCollection)

    # Process pits collection
    collection_in = db_in[PIT_COLLECTION_NAME]
    if PIT_COLLECTION_NAME in db_out.list_collection_names():
        db_out.drop_collection(PIT_COLLECTION_NAME)
    collection_out = db_out.create_collection(PIT_COLLECTION_NAME)
    collection_out.create_index([("location", GEOSPHERE)])

    perform_largescale_conversion_with_pydantic(collection_in, collection_out, PitsCollection)



if __name__ == "__main__":
    main()
