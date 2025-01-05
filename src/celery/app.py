from celery import Celery

from src.celery.processors.diviner_processor import DivinerProcessor
from src.config.celery_config import CELERY_APP_NAME, CELERY_REDIS_CONNECTION_STRING

app = Celery(
    CELERY_APP_NAME,
    broker=CELERY_REDIS_CONNECTION_STRING,
)


diviner_task = app.task(
    DivinerProcessor.process, name="process_diviner_dataset", autoretry_for=(Exception,), retry_backoff=True
)
