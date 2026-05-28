"""Rule data model + matching dispatch."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from skillops_forge.models import SecurityFinding, Severity, SkillFile
from skillops_forge.scanner.heuristics import (
    detect_high_entropy_base64,
    detect_unallowlisted_exfil,
    detect_zero_width,
)

_VALID_TARGETS: frozenset[str] = frozenset({"body", "frontmatter", "examples", "all"})
_VALID_ENGINES: frozenset[str] = frozenset({"regex", "keyword", "heuristic"})


class Rule(BaseModel):
    """A single security rule loaded from YAML."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    severity: Severity
    engine: str
    pattern: str
    targets: tuple[str, ...] = Field(default_factory=lambda: ("body",))
    message: str = ""
    remediation: str = ""

    @field_validator("engine")
    @classmethod
    def _check_engine(cls, value: str) -> str:
        if value not in _VALID_ENGINES:
            raise ValueError(f"engine must be one of {_VALID_ENGINES}, got {value!r}")
        return value

    @field_validator("targets")
    @classmethod
    def _check_targets(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            return ("body",)
        for t in value:
            if t not in _VALID_TARGETS:
                raise ValueError(f"target must be one of {_VALID_TARGETS}, got {t!r}")
        return tuple(value)

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def match(self, skill: SkillFile) -> list[SecurityFinding]:
        """Return all :class:`SecurityFinding` produced by applying this rule."""
        findings: list[SecurityFinding] = []
        for label, text in self._iter_targets(skill):
            findings.extend(self._match_text(skill, text, target_label=label))
        return findings

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _iter_targets(self, skill: SkillFile) -> list[tuple[str, str]]:
        """Yield (label, text) pairs to scan based on ``self.targets``."""
        wants = set(self.targets)
        out: list[tuple[str, str]] = []
        if "all" in wants or "body" in wants:
            out.append(("body", skill.body))
        if "all" in wants or "frontmatter" in wants:
            out.append(("frontmatter", _flatten_frontmatter(skill.frontmatter)))
        if "all" in wants or "examples" in wants:
            for ex in skill.examples:
                out.append(("examples", ex.input))
        return out

    def _match_text(
        self,
        skill: SkillFile,
        text: str,
        *,
        target_label: str,
    ) -> list[SecurityFinding]:
        if not text:
            return []
        if self.engine in {"regex", "keyword"}:
            return self._match_regex(skill, text, target_label=target_label)
        if self.engine == "heuristic":
            return self._match_heuristic(skill, text, target_label=target_label)
        return []

    def _match_regex(
        self,
        skill: SkillFile,
        text: str,
        *,
        target_label: str,
    ) -> list[SecurityFinding]:
        try:
            compiled = re.compile(self.pattern, re.MULTILINE)
        except re.error as exc:  # pragma: no cover - rule authoring error
            raise ValueError(f"bad regex in rule {self.id}: {exc}") from exc
        out: list[SecurityFinding] = []
        for m in compiled.finditer(text):
            line, col = _line_col(text, m.start())
            # ``frontmatter`` and ``examples`` targets feed _match_text a
            # synthetic, flattened string. Reporting their virtual line/col
            # would mislead reviewers (the number does not match the
            # SKILL.md source). Fall back to (0, 0) so the report shows
            # "<unknown location>" rather than a wrong number.
            if target_label in {"frontmatter", "examples"}:
                line, col = 0, 0
            matched = m.group(0)
            out.append(
                SecurityFinding(
                    id=self.id,
                    rule_id=self.id,
                    severity=self.severity,
                    message=self.message or self.name,
                    file=skill.path,
                    line=line,
                    column=col,
                    remediation=self.remediation,
                    category=target_label,
                    matched_text=_truncate(matched),
                    engine=self.engine,
                )
            )
        return out

    def _match_heuristic(
        self,
        skill: SkillFile,
        text: str,
        *,
        target_label: str,
    ) -> list[SecurityFinding]:
        out: list[SecurityFinding] = []
        if self.pattern == "zero_width":
            for hit in detect_zero_width(text):
                out.append(self._mk(skill, hit, target_label))
        elif self.pattern == "high_entropy_base64":
            for hit in detect_high_entropy_base64(text):
                out.append(self._mk(skill, hit, target_label))
        elif self.pattern == "exfil_unallowed_domain":
            for hit in detect_unallowlisted_exfil(text):
                out.append(self._mk(skill, hit, target_label))
        return out

    def _mk(
        self,
        skill: SkillFile,
        hit: tuple[int, int, str],
        target_label: str,
    ) -> SecurityFinding:
        line, col, matched = hit
        # See _match_regex: virtual (frontmatter / examples) text spaces have
        # line numbers that don't map back to the SKILL.md source, so we set
        # location to (0, 0) — "<unknown location>" — to avoid false precision.
        if target_label in {"frontmatter", "examples"}:
            line, col = 0, 0
        return SecurityFinding(
            id=self.id,
            rule_id=self.id,
            severity=self.severity,
            message=self.message or self.name,
            file=skill.path,
            line=line,
            column=col,
            remediation=self.remediation,
            category=target_label,
            matched_text=_truncate(matched),
            engine=self.engine,
        )


def _flatten_frontmatter(fm: dict[str, Any]) -> str:
    """Flatten a frontmatter dict into a searchable string."""
    if not fm:
        return ""
    parts: list[str] = []
    for k, v in fm.items():
        parts.append(f"{k}: {v}")
    return "\n".join(parts)


def _line_col(text: str, offset: int) -> tuple[int, int]:
    """Convert a 0-based offset into a 1-based (line, column) pair."""
    if offset <= 0:
        return 1, 1
    head = text[:offset]
    line = head.count("\n") + 1
    last_nl = head.rfind("\n")
    col = offset - last_nl if last_nl >= 0 else offset + 1
    return line, col


def _truncate(text: str, limit: int = 120) -> str:
    text = text.replace("\n", "\\n")
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text
