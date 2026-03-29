class ResumeAgentError(Exception):
    """Base exception for the application."""


class JobNotFoundError(ResumeAgentError):
    """Raised when a job cannot be found."""


class ArtifactNotFoundError(ResumeAgentError):
    """Raised when an artifact cannot be found."""


class LLMResponseError(ResumeAgentError):
    """Raised when the LLM response is invalid."""


class LatexCompileError(ResumeAgentError):
    """Raised when xelatex compilation fails."""


class QueueDispatchError(ResumeAgentError):
    """Raised when a background job cannot be dispatched."""
