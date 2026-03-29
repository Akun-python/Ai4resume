from __future__ import annotations

from typing import Dict

from sqlalchemy.orm import Session

from app.domain.enums import ArtifactKind, JobStatus, ResumeSection
from app.domain.schemas import (
    CandidateProfile,
    PresentationOptions,
    ResumeDraft,
    ResumeGenerationRequest,
    SectionRefineRequest,
)
from app.infra.db.repositories import GenerationJobRepository
from app.services.compiler import LatexCompilerService
from app.services.drafting import ResumeDraftingService
from app.services.parser import ResumeParsingService
from app.services.rendering import LatexRenderingService
from app.services.storage import ArtifactStorageService


class JobOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.repository = GenerationJobRepository(db)
        self.parser = ResumeParsingService()
        self.drafter = ResumeDraftingService()
        self.renderer = LatexRenderingService()
        self.compiler = LatexCompilerService()
        self.storage = ArtifactStorageService()

    def create_job(self, payload: ResumeGenerationRequest) -> str:
        job = self.repository.create(input_payload=payload.model_dump(mode="json"))
        self.db.commit()
        return job.id

    def create_regeneration_job(
        self,
        source_job_id: str,
        section: ResumeSection,
        refine_request: SectionRefineRequest | None = None,
    ) -> str:
        source = self.repository.get(source_job_id)
        input_payload = dict(source.input_payload)
        if refine_request:
            input_payload["refine_request"] = refine_request.model_dump(mode="json")
            if refine_request.theme_id:
                input_payload["presentation_options"] = {"theme_id": refine_request.theme_id.value}

        job = self.repository.create(
            input_payload=input_payload,
            parent_job_id=source.id,
            section_to_regenerate=section,
            parsed_profile=source.parsed_profile,
            resume_draft=source.resume_draft,
        )
        self.db.commit()
        return job.id

    def run_generation_pipeline(self, job_id: str) -> None:
        job = self.repository.get(job_id)
        payload = ResumeGenerationRequest.model_validate(job.input_payload)

        self.repository.update_status(job_id, JobStatus.PARSING)
        self.db.commit()

        profile = self.parser.parse(
            raw_experience_text=payload.raw_experience_text,
            job_description=payload.job_description,
            target_role=payload.target_role,
            basic_info=payload.basic_info,
        )
        self.repository.update_payloads(job_id, parsed_profile=profile.model_dump(mode="json"))
        self.db.commit()

        self.repository.update_status(job_id, JobStatus.DRAFTING)
        self.db.commit()

        draft = self.drafter.draft(
            profile=profile,
            job_description=payload.job_description,
            target_role=payload.target_role,
            presentation=payload.presentation_options,
        )
        self.repository.update_payloads(job_id, resume_draft=draft.model_dump(mode="json"))
        self.db.commit()

        self._render_compile_and_persist(job_id, profile, draft)

    def run_regeneration_pipeline(self, job_id: str, section: ResumeSection) -> None:
        job = self.repository.get(job_id)
        payload = ResumeGenerationRequest.model_validate(job.input_payload)
        refine_request = SectionRefineRequest.model_validate(job.input_payload.get("refine_request") or {})
        profile = CandidateProfile.model_validate(job.parsed_profile or {})
        current_draft = ResumeDraft.model_validate(job.resume_draft or {})

        self.repository.update_status(job_id, JobStatus.DRAFTING)
        self.db.commit()

        updated_draft = self.drafter.regenerate_section(
            profile=profile,
            current_draft=current_draft,
            job_description=payload.job_description,
            target_role=payload.target_role,
            section=section,
            presentation=payload.presentation_options,
            refine_request=refine_request if refine_request.model_dump(exclude_none=True) else None,
        )
        self.repository.update_payloads(job_id, resume_draft=updated_draft.model_dump(mode="json"))
        self.db.commit()

        self._render_compile_and_persist(job_id, profile, updated_draft)

    def _render_compile_and_persist(
        self,
        job_id: str,
        profile: CandidateProfile,
        draft: ResumeDraft,
    ) -> None:
        self.repository.update_status(job_id, JobStatus.RENDERING)
        self.db.commit()

        tex_content = self.renderer.render(draft)
        tex_path = self.storage.write_tex(job_id, tex_content)
        json_path = self.storage.write_json(
            job_id,
            {
                "parsed_profile": profile.model_dump(mode="json"),
                "resume_draft": draft.model_dump(mode="json"),
            },
        )

        self.repository.update_status(job_id, JobStatus.COMPILING)
        self.db.commit()

        pdf_path = self.compiler.compile(tex_path)
        artifact_refs: Dict[str, str] = {
            ArtifactKind.JSON.value: json_path,
            ArtifactKind.TEX.value: tex_path,
            ArtifactKind.PDF.value: pdf_path,
        }
        self.repository.update_payloads(job_id, artifact_refs=artifact_refs)
        self.repository.update_status(job_id, JobStatus.SUCCEEDED)
        self.db.commit()
