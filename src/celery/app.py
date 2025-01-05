from celery import Celery
from src.config.celery_config import CELERY_APP_NAME
from src.config.mongo_config import MONGO_URI

app = Celery(
    CELERY_APP_NAME,
    broker=MONGO_URI,
)
