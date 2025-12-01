import os
from celery import Celery


celery_app = Celery(
    "ai_netapp",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    include=['app.workers.tasks']
)

celery_app.conf.update(
    # Serialize data as JSON (standard, safe)
    task_serializer="json",
    accept_content=["json"], 
    result_serializer="json",
    
    # Timezone settings
    timezone="UTC",
    enable_utc=True,
    
    # Optimization: If the task fails, don't keep retrying forever unless specified
    task_acks_late=True,
    
    # Tracking: Allows the "Pizza Tracker" to see "STARTED" state, not just PENDING/SUCCESS
    task_track_started=True,
    task_time_limit=30 * 60, # Hard kill task if it runs over 30 mins

)


