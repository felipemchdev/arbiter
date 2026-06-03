from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "arbiter",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-stale-pipelines-every-10-minutes": {
            "task": "app.workers.tasks.check_stale_pipelines",
            "schedule": 600.0,
        }
    },
)