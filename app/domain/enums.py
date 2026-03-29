from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    DRAFTING = "drafting"
    RENDERING = "rendering"
    COMPILING = "compiling"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ResumeSection(str, Enum):
    SUMMARY = "summary"
    SKILLS = "skills"
    PROJECTS = "projects"
    EXPERIENCE = "experience"
    EDUCATION = "education"


class ArtifactKind(str, Enum):
    JSON = "json"
    TEX = "tex"
    PDF = "pdf"


class ThemeId(str, Enum):
    EXECUTIVE_BLUE = "executive_blue"
    FOREST_SLATE = "forest_slate"
    TERRACOTTA_INK = "terracotta_ink"


class RefinePreset(str, Enum):
    MORE_PROFESSIONAL = "more_professional"
    MORE_CONCISE = "more_concise"
    MORE_RESULTS_FOCUSED = "more_results_focused"
    MORE_ROLE_ALIGNED = "more_role_aligned"
    MORE_EXECUTIVE = "more_executive"
