from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ArtifactKind, JobStatus, RefinePreset, ResumeSection, ThemeId


class BasicInfo(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    links: List[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    school: str
    degree: Optional[str] = None
    major: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    company: str
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    name: str
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class SkillEntry(BaseModel):
    category: str
    items: List[str] = Field(default_factory=list)


class AwardEntry(BaseModel):
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None


class CandidateProfile(BaseModel):
    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    education: List[EducationEntry] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    skills: List[SkillEntry] = Field(default_factory=list)
    awards: List[AwardEntry] = Field(default_factory=list)


class PresentationOptions(BaseModel):
    theme_id: ThemeId = ThemeId.EXECUTIVE_BLUE


class PreviewSection(BaseModel):
    section: ResumeSection
    title: str
    order: int


class SectionRefineRequest(BaseModel):
    preset: Optional[RefinePreset] = None
    custom_instruction: Optional[str] = None
    theme_id: Optional[ThemeId] = None


class ResumeDraft(BaseModel):
    selected_sections: List[ResumeSection] = Field(default_factory=list)
    section_content: Dict[str, str] = Field(default_factory=dict)
    latex_context: Dict[str, object] = Field(default_factory=dict)
    template_version: str = "resume_cn_v1"


class ResumeGenerationRequest(BaseModel):
    raw_experience_text: str = Field(min_length=1)
    job_description: str = Field(min_length=1)
    target_role: str = Field(min_length=1)
    basic_info: Optional[BasicInfo] = None
    presentation_options: PresentationOptions = Field(default_factory=PresentationOptions)


class JobArtifactRefs(BaseModel):
    json_path: Optional[str] = Field(default=None, alias="json")
    tex_path: Optional[str] = Field(default=None, alias="tex")
    pdf_path: Optional[str] = Field(default=None, alias="pdf")


class GenerationJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    parent_job_id: Optional[str] = None
    section_to_regenerate: Optional[ResumeSection] = None
    status: JobStatus
    input_payload: Dict[str, object]
    parsed_profile: Optional[Dict[str, object]] = None
    resume_draft: Optional[Dict[str, object]] = None
    artifact_refs: JobArtifactRefs = Field(default_factory=JobArtifactRefs)
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    job_id: str
    parent_job_id: Optional[str] = None
    section_to_regenerate: Optional[ResumeSection] = None
    status: JobStatus
    error_message: Optional[str] = None
    available_sections: List[ResumeSection] = Field(default_factory=list)
    artifacts: Dict[ArtifactKind, Optional[str]] = Field(default_factory=dict)
    parsed_profile_summary: Dict[str, int] = Field(default_factory=dict)
    presentation: PresentationOptions = Field(default_factory=PresentationOptions)
    preview_sections: List[PreviewSection] = Field(default_factory=list)
    updated_at: datetime
