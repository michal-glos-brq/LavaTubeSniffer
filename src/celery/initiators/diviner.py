"""
This is basically a webcrawler, crawling diviner dataset servers, creating tasks for celery workers with
the intent to extract data from the diviner dataset servers from specific locations.
"""


from celery_app import app


def initi_dataset_sweep():
    """
    This function is responsible for initiating the dataset sweep.
    """

    # TODO: Copy from notebook and just instead of processing, create a task
