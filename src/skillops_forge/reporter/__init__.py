"""Reporter package — Markdown / HTML / JSON renderers."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from skillops_forge.config import REPORT_FILENAMES
from skillops_forge.models import SkillReport
from skillops_forge.reporter.html import render_html
from skillops_forge.reporter.json_report import render_json
from skillops_forge.reporter.markdown import render_markdown

ReportFormat = Literal["md", "html", "json", "all"]


def render(report: SkillReport, fmt: ReportFormat, out_dir: Path) -> list[Path]:
    """Render ``report`` into ``out_dir`` using one or all formats.

    Args:
        report: The fully populated report.
        fmt: ``md`` | ``html`` | ``json`` | ``all``.
        out_dir: Directory to write into; created if missing.

    Returns:
        Sorted list of absolute paths that were written.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    formats: tuple[str, ...] = ("md", "html", "json") if fmt == "all" else (fmt,)

    for f in formats:
        target = out_dir / REPORT_FILENAMES[f]
        if f == "md":
            target.write_text(render_markdown(report), encoding="utf-8", newline="\n")
        elif f == "html":
            target.write_text(render_html(report), encoding="utf-8", newline="\n")
        elif f == "json":
            target.write_text(render_json(report), encoding="utf-8", newline="\n")
        written.append(target.resolve())
    return sorted(written)


__all__ = ["ReportFormat", "render"]
