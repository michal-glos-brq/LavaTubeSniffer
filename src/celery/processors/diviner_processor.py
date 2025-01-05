import httpx

from src.mongo.interface import Sessions
from src.celery.processors.base_processor import BaseProcessor, app
from src.mongo.interface import Sessions
from src.config.mongo_config import DIVINER_COLLECTION_NAME
from src.celery.app import app

class DivinerProcessor(BaseProcessor):
    """
    This class is used to process the diviner dataset.
    """

    @staticmethod
    @app.task(
        name="process_diviner_dataset", queue="diviner_queue", autoretry_for=(Exception,), retry_backoff=True
    )
    async def process(xml_url: str, tab_url: str, tolerance: int):
        """
        Process the Diviner dataset by parsing metadata and loading tabular data.

        Args:
            xml_url (str): URL to the PDS4 XML file.
            tab_url (str): URL to the .tab file.
            tolerance (int): Radius around the lunar pits to be considered for data collection (Km).
        """

        # Download both files
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", xml_url, timeout=60) as response:
                response.raise_for_status()
                xml_data = await response.aread()

            async with client.stream("GET", tab_url, timeout=60) as response:
                response.raise_for_status()
                tab_data = await response.aread()

        # Parse metadata and load tabular data
        fields = DivinerProcessor.parse_pds4_metadata(xml_data)
        df = DivinerProcessor.load_tab_file(tab_data, fields)

        # Get lunar pits locations
        lunar_pits_locations = Sessions.get_all_pits_points()

        data = DivinerProcessor.assign_points_to_pits(df, lunar_pits_locations, tolerance)
        Sessions.insert_heap_data(data, DIVINER_COLLECTION_NAME)
