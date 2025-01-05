"""
This file serves as a central configuration for Celery workers and related code
"""

#CELERY_BACKEND_DB = "celery_backend"
CELERY_BACKEND_DB = "tasks"
CELERY_APP_NAME = "LunarSniffer"


DIVINER_QUEUE = "diviner_queue"


ALL_QUEUES = [DIVINER_QUEUE]
