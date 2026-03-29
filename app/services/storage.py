from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from app.core.config import get_settings
from app.core.errors import ArtifactNotFoundError


class ArtifactStorageService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def job_dir(self, job_id: str) -> Path:
        path = self.settings.artifact_root / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_json(self, job_id: str, data: Dict[str, Any]) -> str:
        path = self.job_dir(job_id) / "resume.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)

    def write_tex(self, job_id: str, content: str) -> str:
        path = self.job_dir(job_id) / "resume.tex"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def resolve(self, path_value: str) -> Path:
        path = Path(path_value)
        if not path.exists():
            raise ArtifactNotFoundError(f"Artifact does not exist: {path_value}")
        return path
