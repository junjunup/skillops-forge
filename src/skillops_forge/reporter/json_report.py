"""JSON report rendering."""

from __future__ import annotations

from skillops_forge.models import SkillReport


def render_json(report: SkillReport) -> str:
    """Return ``report`` serialized as pretty-printed JSON."""
    return report.to_json() + "\n"


__all__ = ["render_json"]
