from __future__ import annotations

import subprocess
from pathlib import Path

from app.core.config import get_settings
from app.core.errors import LatexCompileError


class LatexCompilerService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def compile(self, tex_path: str) -> str:
        tex_file = Path(tex_path)
        workdir = tex_file.parent
        command = [
            self.settings.latex_compile_command,
            "-interaction=nonstopmode",
            "-halt-on-error",
            tex_file.name,
        ]
        try:
            subprocess.run(
                command,
                cwd=str(workdir),
                check=True,
                capture_output=True,
                text=True,
                timeout=self.settings.latex_timeout_seconds,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
            stderr = getattr(exc, "stderr", None) or str(exc)
            raise LatexCompileError(f"LaTeX compilation failed: {stderr}") from exc

        pdf_path = workdir / f"{tex_file.stem}.pdf"
        if not pdf_path.exists():
            raise LatexCompileError("LaTeX compilation finished without producing a PDF")
        return str(pdf_path)
