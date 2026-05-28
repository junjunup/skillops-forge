"""Adapter protocol — a forward-looking abstraction for multi-platform support.

This module is part of v0.2 groundwork (item H). The current parsers
(:mod:`skillops_forge.parser.skill_md`, ``claude_md``, ``cursor_rules``) are
hardcoded by file pattern; they all conform to this protocol in spirit, and
a future v0.3 release may switch them to plug-in style adapters loaded via
Python entry points (the same mechanism skilllint uses).

Design rule: an adapter answers *only* "what files do I own" and "how do I
read one of those files into a SkillFile". It does not run rules — those
fire from the central pipeline against the unified :class:`SkillFile` model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from skillops_forge.models import SkillFile


@runtime_checkable
class AdapterProtocol(Protocol):
    """Pluggable adapter interface for a single skill platform."""

    def id(self) -> str:
        """Stable identifier (``claude-code`` / ``cursor`` / ``codex`` / …)."""
        ...

    def path_patterns(self) -> tuple[str, ...]:
        """Glob patterns the adapter claims (e.g. ``"**/SKILL.md"``)."""
        ...

    def parse(self, path: Path) -> SkillFile:
        """Parse ``path`` into a normalized :class:`SkillFile`."""
        ...


__all__ = ["AdapterProtocol"]
