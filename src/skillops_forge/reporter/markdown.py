"""Markdown report rendering."""

from __future__ import annotations

from importlib.resources import files

from jinja2 import Environment, FunctionLoader, select_autoescape

from skillops_forge.exceptions import ReportRenderError
from skillops_forge.models import SkillReport
from skillops_forge.reporter._common import build_context

_TEMPLATE_NAME = "report.md.j2"


def _load_template(name: str) -> str | None:
    if name != _TEMPLATE_NAME:
        return None
    return files("skillops_forge.templates").joinpath(_TEMPLATE_NAME).read_text(encoding="utf-8")


def render_markdown(report: SkillReport) -> str:
    """Render the Markdown report as a string."""
    env = Environment(
        loader=FunctionLoader(_load_template),
        autoescape=select_autoescape(disabled_extensions=("md", "j2"), default=False),
        keep_trailing_newline=True,
        trim_blocks=False,
        lstrip_blocks=False,
    )
    try:
        template = env.get_template(_TEMPLATE_NAME)
        return template.render(**build_context(report))
    except Exception as exc:  # pragma: no cover - re-raise as ReportRenderError
        raise ReportRenderError(f"failed to render markdown report: {exc}") from exc


__all__ = ["render_markdown"]
