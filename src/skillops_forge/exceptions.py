"""Custom exception hierarchy for SkillOps Forge.

The hierarchy is intentionally shallow so that CLI exit-code mapping stays
trivial. ``SkillOpsError`` is the single base class users may catch.
"""

from __future__ import annotations


class SkillOpsError(Exception):
    """Base class for every error raised by SkillOps Forge."""


class ParseError(SkillOpsError):
    """Raised when a skill source file cannot be parsed (bad YAML, IO, etc.)."""


class RuleLoadError(SkillOpsError):
    """Raised when a security rule YAML file is malformed or unloadable."""


class ReportRenderError(SkillOpsError):
    """Raised when a Jinja2 template fails to render a report."""


class UserError(SkillOpsError):
    """Raised when CLI arguments / paths supplied by the user are invalid."""
