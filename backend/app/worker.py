"""
Celery worker configuration and task definitions.
"""
import os
from celery import Celery
from app.core.config import settings


# Create Celery app
celery_app = Celery(
    "studagent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,

    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'retry_policy': {'timeout': 5.0}
    },

    # Beat scheduler settings (for periodic tasks)
    beat_schedule={
        'scrape-scholarships': {
            'task': 'app.tasks.scrape_scholarships',
            'schedule': 3600.0,  # Every hour
        },
        'update-matches': {
            'task': 'app.tasks.update_user_matches',
            'schedule': 1800.0,  # Every 30 minutes
        },
        'cleanup-old-data': {
            'task': 'app.tasks.cleanup_old_data',
            'schedule': 86400.0,  # Daily
        },
    },
)


if __name__ == "__main__":
    celery_app.start()