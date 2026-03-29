from celery import Celery

from app.core.config import get_settings


settings = get_settings()

celery_app = Celery(
    "resume_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["worker.tasks"],
)

celery_app.conf.update(
    task_default_queue="resume",
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)
