from __future__ import annotations

from app.core.config import get_settings
from app.core.errors import QueueDispatchError


def dispatch_task(task, *args) -> str:
    settings = get_settings()
    mode = settings.job_dispatch_mode

    if mode == "inline":
        task.apply(args=args, throw=False)
        return "inline"

    try:
        task.delay(*args)
        return "queued"
    except Exception as exc:
        if mode == "auto" and settings.app_env != "production":
            task.apply(args=args, throw=False)
            return "inline"

        raise QueueDispatchError(
            "Failed to dispatch background job. Ensure Redis/Celery are running, "
            "or set JOB_DISPATCH_MODE=inline for local development."
        ) from exc
