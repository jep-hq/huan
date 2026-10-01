from celery import Celery
from app.config import settings

# Initialize Celery app
celery_app = Celery(
    'huan',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,  # Keep results for 1 hour
    broker_connection_retry_on_startup=True,
)

# Optional: Configure task routes
celery_app.conf.task_routes = {
    'app.tasks.run_spark_job': {'queue': 'spark_jobs'},
    'app.tasks.post_process_job': {'queue': 'post_processing'},
}

# Optional: Beat schedule for recurring tasks
celery_app.conf.beat_schedule = {
    # Example: cleanup old jobs every day
    'cleanup-old-jobs': {
        'task': 'app.tasks.cleanup_old_jobs',
        'schedule': 86400.0,  # Every 24 hours
    },
}
