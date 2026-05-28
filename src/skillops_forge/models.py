"""Core pydantic v2 data models for SkillOps Forge.

Every model is **frozen** and forbids extra fields, so contributors can't
accidentally widen the public schema. Path fields are normalized to POSIX
strings on serialization for cross-platform stability.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_serializer, field_validator

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Severity(str, Enum):
    """Finding severity levels (architecture §3 / §7)."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SkillFormat(str, Enum):
    """Supported skill source formats."""

    SKILL_MD = "skill_md"
    CLAUDE_MD = "claude_md"
    CURSOR_RULES = "cursor_rules"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Frozen base
# ---------------------------------------------------------------------------


class _FrozenModel(BaseModel):
    """Common config for all SkillOps Forge models."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=False,  # preserve exact body content
        arbitrary_types_allowed=False,
        populate_by_name=True,
    )


# ---------------------------------------------------------------------------
# Skill model
# ---------------------------------------------------------------------------


class Example(_FrozenModel):
    """A worked example block extracted from a skill source."""

    title: str = ""
    input: str = ""
    expected_output: str = ""
    commands: tuple[str, ...] = Field(default_factory=tuple)
    language: str = ""

    @field_validator("commands", mode="before")
    @classmethod
    def _coerce_commands(cls, value: Any) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, list):
            return tuple(str(c) for c in value)
        if isinstance(value, tuple):
            return value
        raise TypeError("commands must be a list/tuple of strings")


class SkillFile(_FrozenModel):
    """A normalized representation of a single skill source file."""

    path: Path
    format: SkillFormat
    frontmatter: dict[str, Any] = Field(default_factory=dict)
    body: str = ""
    allowed_tools: tuple[str, ...] = Field(default_factory=tuple)
    examples: tuple[Example, ...] = Field(default_factory=tuple)
    sha256: str = ""
    line_count: int = 0
    sections: dict[str, str] = Field(default_factory=dict)
    parse_errors: tuple[str, ...] = Field(default_factory=tuple)

    @field_serializer("path")
    def _serialize_path(self, value: Path) -> str:
        return PurePosixPath(value.as_posix()).as_posix()

    def section(self, name: str) -> str:
        """Return body text under a Markdown ``## section`` (case-insensitive)."""
        lookup = name.strip().lower()
        for key, val in self.sections.items():
            if key.strip().lower() == lookup:
                return val
        return ""

    @staticmethod
    def compute_sha256(text: str) -> str:
        """Return a hex sha256 digest for ``text`` (utf-8)."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SkillInventory(_FrozenModel):
    """The full set of skill files discovered under a target root."""

    root: Path
    files: tuple[SkillFile, ...] = Field(default_factory=tuple)
    scanned_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    tool_version: str = ""

    @field_serializer("root")
    def _serialize_root(self, value: Path) -> str:
        return PurePosixPath(value.as_posix()).as_posix()

    @field_serializer("scanned_at")
    def _serialize_scanned_at(self, value: datetime) -> str:
        return _iso8601_z(value)

    def by_format(self, fmt: SkillFormat) -> tuple[SkillFile, ...]:
        """Return all files matching ``fmt``."""
        return tuple(f for f in self.files if f.format == fmt)

    def to_json(self) -> str:
        """Return the inventory as a JSON string."""
        return self.model_dump_json(indent=2)


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


class Finding(_FrozenModel):
    """Common finding shape shared by Audit and Security findings."""

    id: str
    severity: Severity
    message: str
    file: Path
    line: int = 0
    column: int = 0
    remediation: str = ""
    category: str = ""
    suggestion: str = ""
    docs_url: str = ""

    @field_serializer("file")
    def _serialize_file(self, value: Path) -> str:
        return PurePosixPath(value.as_posix()).as_posix()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dict (path is POSIX string, severity is str)."""
        return cast(dict[str, Any], json.loads(self.model_dump_json()))


class AuditFinding(Finding):
    """Structural-quality finding produced by the auditor."""

    rule_kind: str = ""  # frontmatter | description | permissions | io | examples
    field: str = ""


class SecurityFinding(Finding):
    """Security-rule finding produced by the scanner."""

    rule_id: str = ""
    matched_text: str = ""
    engine: str = "regex"  # regex | keyword | heuristic


# ---------------------------------------------------------------------------
# Runner output
# ---------------------------------------------------------------------------


class ExampleRun(_FrozenModel):
    """Outcome of a single example dry-run."""

    example_title: str = ""
    file: Path
    success: bool = True
    blocked_actions: tuple[SecurityFinding, ...] = Field(default_factory=tuple)
    dry_run_log: str = ""

    @field_serializer("file")
    def _serialize_file(self, value: Path) -> str:
        return PurePosixPath(value.as_posix()).as_posix()


# ---------------------------------------------------------------------------
# Permission summary (RPT-A)
# ---------------------------------------------------------------------------


class PermissionSummary(_FrozenModel):
    """Aggregate read / write / commands / network permissions across a skill.

    Built by the auditor's permission-summary extractor (RPT-A) and surfaced in
    the report header so reviewers can see the union of permissions a skill
    asks for at a glance.
    """

    files_read: tuple[str, ...] = Field(default_factory=tuple)
    files_write: tuple[str, ...] = Field(default_factory=tuple)
    commands: tuple[str, ...] = Field(default_factory=tuple)
    network: tuple[str, ...] = Field(default_factory=tuple)

    def is_empty(self) -> bool:
        """Return True when no permissions were detected."""
        return not (self.files_read or self.files_write or self.commands or self.network)


# ---------------------------------------------------------------------------
# Skill report (root output)
# ---------------------------------------------------------------------------


class SkillReport(_FrozenModel):
    """The full report emitted by the pipeline."""

    inventory: SkillInventory
    audit_findings: tuple[AuditFinding, ...] = Field(default_factory=tuple)
    security_findings: tuple[SecurityFinding, ...] = Field(default_factory=tuple)
    example_runs: tuple[ExampleRun, ...] = Field(default_factory=tuple)
    score: int = 100
    overall_risk: Severity = Severity.INFO
    threshold: int = 70
    generated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    tool_version: str = ""
    target: Path | None = None
    permission_summary: PermissionSummary | None = None

    @field_serializer("target")
    def _serialize_target(self, value: Path | None) -> str | None:
        if value is None:
            return None
        return PurePosixPath(value.as_posix()).as_posix()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_passed(self) -> bool:
        """Pass-fail verdict (computed).

        Rules:
        * Any CRITICAL audit OR security finding → False (one-strike veto).
        * Any CRITICAL action blocked during examples dry-run → False.
        * Otherwise: ``score >= threshold``.
        """
        for finding in self.security_findings:
            if finding.severity == Severity.CRITICAL:
                return False
        for audit in self.audit_findings:
            if audit.severity == Severity.CRITICAL:
                return False
        for run in self.example_runs:
            for blocked in run.blocked_actions:
                if blocked.severity == Severity.CRITICAL:
                    return False
        return self.score >= self.threshold

    @field_serializer("generated_at")
    def _serialize_generated_at(self, value: datetime) -> str:
        return _iso8601_z(value)

    def to_json(self) -> str:
        """Return the report as a JSON string."""
        return self.model_dump_json(indent=2)

    def summary(self) -> dict[str, Any]:
        """Return a small summary dict suitable for CLI rendering."""
        return {
            "score": self.score,
            "overall_risk": self.overall_risk.value,
            "threshold": self.threshold,
            "is_passed": self.is_passed,
            "files": len(self.inventory.files),
            "audit_findings": len(self.audit_findings),
            "security_findings": len(self.security_findings),
            "examples_run": len(self.example_runs),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _iso8601_z(value: datetime) -> str:
    """Serialize a datetime as ISO 8601 with a literal ``Z`` suffix."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


__all__ = [
    "AuditFinding",
    "Example",
    "ExampleRun",
    "Finding",
    "PermissionSummary",
    "SecurityFinding",
    "Severity",
    "SkillFile",
    "SkillFormat",
    "SkillInventory",
    "SkillReport",
]
