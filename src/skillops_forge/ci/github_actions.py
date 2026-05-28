"""GitHub Actions workflow generator."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Literal

from jinja2 import Environment, FunctionLoader, select_autoescape

from skillops_forge import __version__
from skillops_forge.config import (
    DEFAULT_THRESHOLD,
    GH_ACTIONS_CHECKOUT_REF,
    GH_ACTIONS_SETUP_PYTHON_REF,
)
from skillops_forge.exceptions import ReportRenderError

_TEMPLATE_NAME = "ci/skillops.yml.j2"


def _load_template(name: str) -> str | None:
    if name != _TEMPLATE_NAME:
        return None
    return (
        files("skillops_forge.templates")
        .joinpath("ci")
        .joinpath("skillops.yml.j2")
        .read_text(encoding="utf-8")
    )


def render_workflow(*, threshold: int = DEFAULT_THRESHOLD) -> str:
    """Render the GitHub Actions workflow YAML."""
    env = Environment(
        loader=FunctionLoader(_load_template),
        autoescape=select_autoescape(disabled_extensions=("yml", "yaml", "j2"), default=False),
        keep_trailing_newline=True,
    )
    try:
        template = env.get_template(_TEMPLATE_NAME)
        return template.render(
            checkout_ref=GH_ACTIONS_CHECKOUT_REF,
            setup_python_ref=GH_ACTIONS_SETUP_PYTHON_REF,
            tool_version=__version__,
            threshold=threshold,
        )
    except Exception as exc:  # pragma: no cover - re-raise as ReportRenderError
        raise ReportRenderError(f"failed to render CI workflow: {exc}") from exc


def init_ci(
    *,
    provider: Literal["github-actions"] = "github-actions",
    out: Path = Path(".github/workflows/skillops.yml"),
    force: bool = False,
    threshold: int = DEFAULT_THRESHOLD,
) -> Path:
    """Write a GitHub Actions workflow that runs SkillOps Forge.

    Args:
        provider: Currently only ``github-actions`` is supported.
        out: Destination file path.
        force: When False (default), refuses to overwrite existing files (Q7).
        threshold: Score threshold injected into the template.

    Returns:
        The path that was written.

    Raises:
        FileExistsError: When ``out`` exists and ``force`` is False.
    """
    _ = provider  # only one provider for now
    out = Path(out)
    if out.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing file: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    content = render_workflow(threshold=threshold)
    out.write_text(content, encoding="utf-8", newline="\n")
    return out


__all__ = ["init_ci", "render_workflow"]
