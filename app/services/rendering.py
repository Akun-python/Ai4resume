from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from app.domain.schemas import ResumeDraft


def latex_escape(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


class LatexRenderingService:
    def __init__(self) -> None:
        templates_root = Path(__file__).resolve().parents[1] / "templates"
        self.environment = Environment(
            loader=FileSystemLoader(str(templates_root)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.environment.filters["latex_escape"] = latex_escape

    def render(self, draft: ResumeDraft) -> str:
        template = self.environment.get_template(f"{draft.template_version}/resume.tex.j2")
        return template.render(**draft.latex_context)
