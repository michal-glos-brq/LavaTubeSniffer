import httpx
import logging

from src.mongo.interface import Sessions
from src.celery.processors.base_processor import BaseProcessor
from src.mongo.interface import Sessions
from src.config.mongo_config import DIVINER_COLLECTION_NAME


class DivinerProcessor(BaseProcessor):
    """
    This class is used to process the diviner dataset.
    """

    # @staticmethod
    # async def process(xml_url: str, tab_url: str, tolerance: float):
    #     """
    #     Process the Diviner dataset by parsing metadata and loading tabular data.

    #     Args:
    #         xml_url (str): URL to the PDS4 XML file.
    #         tab_url (str): URL to the .tab file.
    #         tolerance (float): Radius around the lunar pits to be considered for data collection (Km).
    #     """
    #     logging.debug(f"Processing {xml_url} and {tab_url}")
    #     # Download both files
    #     async with httpx.AsyncClient() as client:
    #         async with client.stream("GET", xml_url, timeout=60) as response:
    #             response.raise_for_status()
    #             xml_data = await response.aread()

    #         async with client.stream("GET", tab_url, timeout=60) as response:
    #             response.raise_for_status()
    #             tab_data = await response.aread()

    #     # Parse metadata and load tabular data
    #     fields = DivinerProcessor.parse_pds4_metadata(xml_data)
    #     df = DivinerProcessor.load_tab_file(tab_data, fields)

    #     # Get lunar pits locations
    #     lunar_pits_locations = Sessions.get_all_pits_points()

    #     data = DivinerProcessor.assign_points_to_pits(df, lunar_pits_locations, tolerance)
    #     Sessions.insert_heap_data(data, DIVINER_COLLECTION_NAME)
    #     logging.info(f"Inserted data for {xml_url} and {tab_url}")

    @staticmethod
    def process(xml_url: str, tab_url: str, tolerance: float):
        logging.debug(f"Processing {xml_url} and {tab_url}")
        with httpx.Client() as client:
            response = client.get(xml_url, timeout=60)
            response.raise_for_status()
            xml_data = response.content

            response = client.get(tab_url, timeout=60)
            response.raise_for_status()
            tab_data = response.content

        fields = DivinerProcessor.parse_pds4_metadata(xml_data)
        df = DivinerProcessor.load_tab_file(tab_data, fields)

        lunar_pits_locations = Sessions.get_all_pits_points()

        data = DivinerProcessor.assign_points_to_pits(df, lunar_pits_locations, tolerance)
        Sessions.insert_heap_data(data, DIVINER_COLLECTION_NAME)
        logging.info(f"Inserted data for {xml_url} and {tab_url}")
