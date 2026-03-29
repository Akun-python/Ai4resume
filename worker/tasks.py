from __future__ import annotations

from app.core.errors import ResumeAgentError
from app.domain.enums import JobStatus, ResumeSection
from app.infra.db.repositories import GenerationJobRepository
from app.infra.db.session import session_scope
from app.infra.queue.celery_app import celery_app
from app.services.jobs import JobOrchestrator


@celery_app.task(name="worker.generate_resume_job")
def generate_resume_job(job_id: str) -> None:
    with session_scope() as db:
        orchestrator = JobOrchestrator(db)
        repository = GenerationJobRepository(db)
        try:
            orchestrator.run_generation_pipeline(job_id)
        except ResumeAgentError as exc:
            repository.update_status(job_id, JobStatus.FAILED, error_message=str(exc))
            db.commit()
            raise
        except Exception as exc:
            repository.update_status(job_id, JobStatus.FAILED, error_message=f"Unexpected error: {exc}")
            db.commit()
            raise


@celery_app.task(name="worker.regenerate_resume_section_job")
def regenerate_resume_section_job(job_id: str, section: str) -> None:
    with session_scope() as db:
        orchestrator = JobOrchestrator(db)
        repository = GenerationJobRepository(db)
        try:
            orchestrator.run_regeneration_pipeline(job_id, ResumeSection(section))
        except ResumeAgentError as exc:
            repository.update_status(job_id, JobStatus.FAILED, error_message=str(exc))
            db.commit()
            raise
        except Exception as exc:
            repository.update_status(job_id, JobStatus.FAILED, error_message=f"Unexpected error: {exc}")
            db.commit()
            raise
