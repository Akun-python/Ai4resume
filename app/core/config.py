from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv


load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=False)


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_host: str
    app_port: int
    database_url: str
    redis_url: str
    cors_allow_origins: List[str]
    openai_base_url: str
    openai_api_key: str
    openai_model: str
    artifact_root: Path
    latex_compile_command: str
    latex_timeout_seconds: int
    celery_task_always_eager: bool
    job_dispatch_mode: str


def _as_list(value: str | None, default: List[str]) -> List[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _normalized_base_url() -> str:
    base_url = (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("APIYI_BASE_URL")
        or "https://api.openai.com/v1"
    ).strip()
    if base_url.endswith("/chat/completions"):
        base_url = base_url[: -len("/chat/completions")]
    return base_url.rstrip("/")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    artifact_root = Path(os.getenv("ARTIFACT_ROOT", "data/artifacts")).resolve()
    artifact_root.mkdir(parents=True, exist_ok=True)
    return Settings(
        app_name=os.getenv("APP_NAME", "resume-agent-backend"),
        app_env=os.getenv("APP_ENV", "development"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./resume_agent.db"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        cors_allow_origins=_as_list(
            os.getenv("CORS_ALLOW_ORIGINS"),
            default=[
                "http://127.0.0.1:5173",
                "http://localhost:5173",
                "http://127.0.0.1:5174",
                "http://localhost:5174",
                "http://127.0.0.1:4173",
                "http://localhost:4173",
            ],
        ),
        openai_base_url=_normalized_base_url(),
        openai_api_key=(os.getenv("OPENAI_API_KEY") or os.getenv("APIYI_API_KEY") or "").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        artifact_root=artifact_root,
        latex_compile_command=os.getenv("LATEX_COMPILE_COMMAND", "xelatex"),
        latex_timeout_seconds=int(os.getenv("LATEX_TIMEOUT_SECONDS", "60")),
        celery_task_always_eager=_as_bool(os.getenv("CELERY_TASK_ALWAYS_EAGER"), default=False),
        job_dispatch_mode=os.getenv("JOB_DISPATCH_MODE", "auto").strip().lower(),
    )
