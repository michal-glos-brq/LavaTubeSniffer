


from celery_app import app

from src.celery.cache import get_lunar_pit_locations

@app.task(name='process_diviner_data')
def process_diviner_data(url: str, tollerance: float = 0.1):
    """
    This a Celery task is responsible for processing the diviner dataset.

    Args:
        url (str): The URL of SPICE file of DIVINER dataset
        tollerance (float): The radius of the area around the pit to be considered
    """
    lunar_pit_locations = get_lunar_pit_locations()
    # Download the SPICE file
    # Decide whether holds data of interest 
    # Extract data of interest

