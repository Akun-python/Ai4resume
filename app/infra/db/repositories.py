from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.errors import JobNotFoundError
from app.domain.enums import JobStatus, ResumeSection
from app.infra.db.models import GenerationJobModel


class GenerationJobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        input_payload: dict,
        parent_job_id: Optional[str] = None,
        section_to_regenerate: Optional[ResumeSection] = None,
        parsed_profile: Optional[dict] = None,
        resume_draft: Optional[dict] = None,
    ) -> GenerationJobModel:
        job = GenerationJobModel(
            input_payload=input_payload,
            parent_job_id=parent_job_id,
            section_to_regenerate=section_to_regenerate.value if section_to_regenerate else None,
            parsed_profile=parsed_profile,
            resume_draft=resume_draft,
            artifact_refs={},
        )
        self.db.add(job)
        self.db.flush()
        self.db.refresh(job)
        return job

    def get(self, job_id: str) -> GenerationJobModel:
        job = self.db.get(GenerationJobModel, job_id)
        if not job:
            raise JobNotFoundError(f"Job {job_id} not found")
        return job

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: Optional[str] = None,
    ) -> GenerationJobModel:
        job = self.get(job_id)
        job.status = status.value
        job.error_message = error_message
        self.db.add(job)
        self.db.flush()
        self.db.refresh(job)
        return job

    def update_payloads(
        self,
        job_id: str,
        parsed_profile: Optional[dict] = None,
        resume_draft: Optional[dict] = None,
        artifact_refs: Optional[dict] = None,
    ) -> GenerationJobModel:
        job = self.get(job_id)
        if parsed_profile is not None:
            job.parsed_profile = parsed_profile
        if resume_draft is not None:
            job.resume_draft = resume_draft
        if artifact_refs is not None:
            job.artifact_refs = artifact_refs
        self.db.add(job)
        self.db.flush()
        self.db.refresh(job)
        return job
