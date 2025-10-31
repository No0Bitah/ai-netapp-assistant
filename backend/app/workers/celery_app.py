import os
from celery import Celery


celery_app = Celery(
    "ai_netapp",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
)


@celery_app.task
def ping():
    return "pong"