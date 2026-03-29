from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.core.errors import ArtifactNotFoundError, JobNotFoundError, QueueDispatchError
from app.domain.enums import ArtifactKind, JobStatus, ResumeSection
from app.domain.schemas import (
    JobCreateResponse,
    JobStatusResponse,
    PreviewSection,
    PresentationOptions,
    ResumeGenerationRequest,
    SectionRefineRequest,
)
from app.infra.db.repositories import GenerationJobRepository
from app.infra.queue.dispatcher import dispatch_task
from app.services.jobs import JobOrchestrator
from app.services.storage import ArtifactStorageService
from worker.tasks import generate_resume_job, regenerate_resume_section_job


router = APIRouter(prefix="/v1/resume/jobs", tags=["resume"])


@router.post("", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job(payload: ResumeGenerationRequest, db: Session = Depends(get_session)) -> JobCreateResponse:
    job_id = JobOrchestrator(db).create_job(payload)
    try:
        dispatch_task(generate_resume_job, job_id)
    except QueueDispatchError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return JobCreateResponse(job_id=job_id, status=JobStatus.PENDING)


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str, db: Session = Depends(get_session)) -> JobStatusResponse:
    repository = GenerationJobRepository(db)
    try:
        job = repository.get(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    sections = []
    presentation = PresentationOptions()
    preview_sections: list[PreviewSection] = []
    if job.resume_draft:
        sections = [ResumeSection(section) for section in job.resume_draft.get("selected_sections", [])]
        latex_context = job.resume_draft.get("latex_context", {})
        presentation = PresentationOptions.model_validate(latex_context.get("presentation") or {})
        preview_sections = [
            PreviewSection.model_validate(item) for item in latex_context.get("preview_sections", [])
        ]
    elif job.input_payload:
        presentation = PresentationOptions.model_validate(job.input_payload.get("presentation_options") or {})

    parsed_profile = job.parsed_profile or {}
    summary = {
        "education_count": len(parsed_profile.get("education", [])),
        "experience_count": len(parsed_profile.get("experience", [])),
        "project_count": len(parsed_profile.get("projects", [])),
        "skill_group_count": len(parsed_profile.get("skills", [])),
    }
    artifacts = {kind: job.artifact_refs.get(kind.value) for kind in ArtifactKind}

    return JobStatusResponse(
        job_id=job.id,
        parent_job_id=job.parent_job_id,
        section_to_regenerate=ResumeSection(job.section_to_regenerate) if job.section_to_regenerate else None,
        status=JobStatus(job.status),
        error_message=job.error_message,
        available_sections=sections,
        artifacts=artifacts,
        parsed_profile_summary=summary,
        presentation=presentation,
        preview_sections=preview_sections,
        updated_at=job.updated_at,
    )


@router.get("/{job_id}/artifacts/{kind}")
def download_artifact(job_id: str, kind: ArtifactKind, db: Session = Depends(get_session)) -> FileResponse:
    repository = GenerationJobRepository(db)
    storage = ArtifactStorageService()
    try:
        job = repository.get(job_id)
        path_value = job.artifact_refs.get(kind.value)
        if not path_value:
            raise ArtifactNotFoundError(f"Artifact {kind.value} is not available for job {job_id}")
        path = storage.resolve(path_value)
    except (JobNotFoundError, ArtifactNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    media_type = {
        ArtifactKind.JSON: "application/json",
        ArtifactKind.TEX: "application/x-tex",
        ArtifactKind.PDF: "application/pdf",
    }[kind]
    if kind == ArtifactKind.PDF:
        response = FileResponse(Path(path), media_type=media_type)
        response.headers["Content-Disposition"] = f'inline; filename="{Path(path).name}"'
        return response
    return FileResponse(Path(path), media_type=media_type, filename=Path(path).name)


@router.post(
    "/{job_id}/sections/{section}/regenerate",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def regenerate_section(
    job_id: str,
    section: ResumeSection,
    payload: Optional[SectionRefineRequest] = Body(default=None),
    db: Session = Depends(get_session),
) -> JobCreateResponse:
    repository = GenerationJobRepository(db)
    try:
        source_job = repository.get(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if source_job.status != JobStatus.SUCCEEDED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only succeeded jobs can be used for section regeneration",
        )

    new_job_id = JobOrchestrator(db).create_regeneration_job(job_id, section, payload)
    try:
        dispatch_task(regenerate_resume_section_job, new_job_id, section.value)
    except QueueDispatchError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return JobCreateResponse(job_id=new_job_id, status=JobStatus.PENDING)
