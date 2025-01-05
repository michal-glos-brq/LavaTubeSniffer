"""
This code scrapes the Lunar Pits database and saves it into a MongoDB database.
"""
import os
import requests
from time import sleep

from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from pymongo import MongoClient

from src.config.mongo_config import (
    IMG_BASE_FOLDER,
    MONGO_URI,
    PIT_ATLAS_DB_NAME,
    PIT_COLLECTION_NAME,
    PIT_DETAIL_COLLECTION_NAME,
    IMAGE_COLLECTION_NAME,
    PIT_TABLE_COLUMNS,
    PIT_ATLAS_LIST_URL,
    PIT_ATLAS_BASE_URL,
    BROWSER_HEADERS,
    REQUEST_MAX_RETRIES,
    EXPECTED_PIT_TABLE_COLUMNS,
    INITIAL_DOWNLOAD_RESET_TIME_SECONDS,
    BROWSER_HEADERS,
)


def fetch_with_retries(url, headers, REQUEST_MAX_RETRIES=REQUEST_MAX_RETRIES, pbar=None):
    """Fetch a URL with retry logic."""
    sleep_time = INITIAL_DOWNLOAD_RESET_TIME_SECONDS
    for _ in range(REQUEST_MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response
        except:
            if pbar:
                pbar.set_description(f"Retrying - {sleep_time} s")
            else:
                print(f"Retrying in {sleep_time} seconds.")
            sleep(sleep_time)
            sleep_time *= 2
    return None


def parse_table_headers(table):
    """
    Extract headers from a table.
    """
    return [header.text.strip() for header in table.find("thead").find_all("th")]


def parse_table_rows(table):
    """Extract rows of data from a table."""
    rows = table.find("tbody").find_all("tr")
    data = []
    for row in rows:
        cells = row.find_all("td")
        cell_data = []
        object_link = None
        for cell in cells:
            link = cell.find("a")
            if link:
                cell_data.append(cell.text.strip())
                object_link = link["href"]
            else:
                cell_data.append(cell.text.strip())
        cell_data.append(object_link)
        data.append(cell_data)
    return data


def download_image(image_url, pbar=None):
    """Download an image and save it locally."""
    img_response = fetch_with_retries(image_url, BROWSER_HEADERS, pbar=pbar)
    if img_response:
        image_name = os.path.basename(image_url)
        image_path = os.path.join(IMG_BASE_FOLDER, image_name)
        with open(image_path, "wb") as img_file:
            img_file.write(img_response.content)
        return image_path
    return None


def parse_details_and_images(divs, row_name, pbar=None):
    """Parse details and images from the detail page."""
    # Parse details table
    detail_table = divs[0].find("table")
    detail_rows = detail_table.find_all("tr")
    parsed_details = {
        detail.find("th").text.strip().replace(".", "").replace(" ", "_").lower(): detail.find("td").text.strip()
        for detail in detail_rows[1:]
    }
    parsed_details["origin"] = detail_rows[0].find("th").text.strip().split(":")[0].strip()
    parsed_details["name"] = row_name

    # Parse images and related metadata
    image_data = []
    images_tables = divs[1].find_all("table")
    for image_table in images_tables:
        image_detail = {"title": image_table.find("th").text.strip(), "object": row_name}
        for dato in image_table.find_all("tr"):
            if dato.find("td"):
                if dato.find("th"):
                    key = dato.find("th").text.strip().replace(".", "").replace(" ", "_").lower()
                    value = dato.find("td").text.strip()
                    image_detail[key] = value
                elif img := dato.find("img"):
                    image_url = f"{PIT_ATLAS_BASE_URL}{img['src']}"
                    image_path = download_image(image_url, pbar=pbar)
                    if image_path:
                        image_detail["image_path"] = image_path
        image_data.append(image_detail)
    return parsed_details, image_data


def replace_collection(collection_name, df, db):
    """Rewrites a collection by dataframe data"""
    collection = db[collection_name]
    # Drop the existing collection
    collection.drop()
    # Insert the new DataFrame
    records = df.to_dict(orient="records")  # Convert DataFrame to list of dicts
    collection.insert_many(records)
    print(f"Replaced collection '{collection_name}' with {len(records)} records.")


# Main Script
def scrape_lunar_pit_atlas():
    # Ensure image folder exists
    os.makedirs(IMG_BASE_FOLDER, exist_ok=True)
    # Connect to Mongo DB
    client = MongoClient(MONGO_URI)
    db = client[PIT_ATLAS_DB_NAME]
    # Fetch main list page
    response = requests.get(PIT_ATLAS_LIST_URL, headers=BROWSER_HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch the list page. Status code: {response.status_code}")
        exit()

    # Parse main page for pit objects
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", {"id": "pitsTable"})
    headers = parse_table_headers(table)
    if headers != EXPECTED_PIT_TABLE_COLUMNS:
        raise ValueError("Table headers have changed. Please update the script.")

    rows_data = parse_table_rows(table)
    general_df = pd.DataFrame(rows_data, columns=PIT_TABLE_COLUMNS)

    detail_data = []
    image_data = []

    # Fetch detailed pages and parse
    pbar = tqdm(total=general_df.shape[0], desc="Fetching Details", ncols=100)
    for _, row in general_df.iterrows():
        pbar.set_description("Fetching Details ...")
        detail_url = f'{PIT_ATLAS_BASE_URL}{row["link_suffix"]}'
        detail_response = fetch_with_retries(detail_url, BROWSER_HEADERS, pbar=pbar)
        if not detail_response:
            print(f"Failed to fetch details for {row['name']}")
            continue

        detail_soup = BeautifulSoup(detail_response.content, "html.parser")
        divs = detail_soup.find_all("div", {"class": "table-responsive"})
        if len(divs) < 2:
            print(f"Unexpected structure for {row['name']}. Skipping.")
            continue

        parsed_details, parsed_images = parse_details_and_images(divs, row["name"], pbar=pbar)
        detail_data.append(parsed_details)
        image_data.extend(parsed_images)
        pbar.update(1)

    pbar.close()

    # Convert to DataFrames
    detail_df = pd.DataFrame(detail_data)
    image_df = pd.DataFrame(image_data)

    # Replace collections in MongoDB
    print("Replacing PITS collection in MongoDB ...")
    replace_collection(PIT_COLLECTION_NAME, general_df, db)
    print("Replacing PIT_DETAILS and IMAGES collections in MongoDB ...")
    replace_collection(PIT_DETAIL_COLLECTION_NAME, detail_df, db)
    print("Replacing IMAGES collection in MongoDB ...")
    replace_collection(IMAGE_COLLECTION_NAME, image_df, db)
    print("Done.")


if __name__ == "__main__":
    scrape_lunar_pit_atlas()
