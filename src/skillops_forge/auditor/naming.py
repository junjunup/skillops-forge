"""Audit: frontmatter naming + content quality (Anthropic-aligned).

Inspired by:
    * skillcheck rules/frontmatter.py (kebab-case, person voice, XML tags)
    * skilllint rules/sk_series.py (SK001-SK005 — strict name pattern,
      description length range, multi-line YAML hint)

These rules are emitted in addition to the basic existence checks already
performed by :mod:`skillops_forge.auditor.frontmatter`.
"""

from __future__ import annotations

import re

from skillops_forge.models import AuditFinding, Severity, SkillFile, SkillFormat

# ---------------------------------------------------------------------------
# Constants (sourced from the official Anthropic skill spec / spec constants)
# ---------------------------------------------------------------------------

# Lowercase alphanumeric with single hyphens. No leading/trailing/consecutive.
# Matches:  abc / a-b / a-b-c / a1 / 1a / a-1-b
# Rejects:  -a / a- / a--b / Aa / a_b / a@b
_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

NAME_MAX_LEN: int = 64
DESCRIPTION_MAX_LEN: int = 1024
DESCRIPTION_MIN_LEN: int = 20

# Reserved roots — skill names cannot use these brand prefixes.
_RESERVED_NAME_TOKENS: frozenset[str] = frozenset(
    {"anthropic", "claude", "openai", "cursor", "codex"}
)

# Allowed frontmatter fields per Anthropic SKILL.md spec + Claude Code agents.
_KNOWN_FRONTMATTER_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "description",
        "version",
        "author",
        "source",
        "tags",
        "allowed-tools",
        "model",
        "context",
        "agent",
        "hooks",
        "user-invocable",
        "disable-model-invocation",
        "skills",
        "trigger_words",
        "license",
    }
)

# Disallow embedded markup in description.
_XML_TAG_RE = re.compile(r"<[a-zA-Z/][^>]*>")

# First-person voice (Anthropic style guideline).
_FIRST_PERSON_RE = re.compile(
    r"(?:(?:^|(?<=\.\s))I\b)"
    r"|\bI (?:can|will|am|do|have|would|should|need|shall|won't|didn't|don't)\b"
    r"|\bMy\b",
    re.MULTILINE,
)
_SECOND_PERSON_RE = re.compile(r"\b[Yy]ou (?:can|will|should|must|need|are|have|do|get|use)\b")

# 11-entry trigger-phrase list (skilllint SK005).
_TRIGGER_PHRASES: tuple[str, ...] = (
    "use when",
    "use this",
    "use on",
    "used when",
    "used by",
    "when ",
    "trigger",
    "activate",
    "load this",
    "load when",
    "invoke",
)


def _has_trigger_phrase(text: str) -> bool:
    """Return True if *text* contains any documented trigger phrase."""
    lowered = text.lower()
    return any(phrase in lowered for phrase in _TRIGGER_PHRASES)


def audit_naming(skill: SkillFile) -> list[AuditFinding]:
    """Strict naming + content audits for SKILL.md (no-op for other formats)."""
    if skill.format != SkillFormat.SKILL_MD:
        return []
    if skill.parse_errors:
        return []  # frontmatter audit already emitted AUD-000

    fm = skill.frontmatter or {}
    findings: list[AuditFinding] = []

    findings.extend(_check_name(skill, fm))
    findings.extend(_check_description(skill, fm))
    findings.extend(_check_unknown_fields(skill, fm))

    return findings


# ---------------------------------------------------------------------------
# Name rules — AUD-110, AUD-111, AUD-112, AUD-113
# ---------------------------------------------------------------------------


def _check_name(skill: SkillFile, fm: dict[str, object]) -> list[AuditFinding]:
    name = fm.get("name")
    if not isinstance(name, str) or not name:
        return []  # absence is reported by the existing frontmatter audit
    out: list[AuditFinding] = []

    # AUD-110 kebab-case format.
    if not _NAME_RE.match(name):
        problems: list[str] = []
        if any(c.isupper() for c in name):
            problems.append("uppercase characters")
        if "_" in name:
            problems.append("underscores")
        if name.startswith("-"):
            problems.append("leading hyphen")
        if name.endswith("-"):
            problems.append("trailing hyphen")
        if "--" in name:
            problems.append("consecutive hyphens")
        if not problems:
            problems.append("invalid characters")
        suggestion = re.sub(r"_", "-", name).lower().strip("-").replace("--", "-")
        out.append(
            AuditFinding(
                id="AUD-110",
                severity=Severity.HIGH,
                message=(
                    f"name '{name}' is not kebab-case ({', '.join(problems)}); "
                    f"the spec requires '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'."
                ),
                file=skill.path,
                rule_kind="frontmatter",
                field="name",
                remediation=f"Rename to lowercase kebab-case, e.g. '{suggestion}'.",
                category="frontmatter",
            )
        )

    # AUD-111 length.
    if len(name) > NAME_MAX_LEN:
        out.append(
            AuditFinding(
                id="AUD-111",
                severity=Severity.HIGH,
                message=f"name length {len(name)} exceeds the spec maximum of {NAME_MAX_LEN}.",
                file=skill.path,
                rule_kind="frontmatter",
                field="name",
                remediation=f"Shorten the name to ≤ {NAME_MAX_LEN} characters.",
                category="frontmatter",
            )
        )

    # AUD-112 reserved tokens.
    lowered = name.lower()
    for token in _RESERVED_NAME_TOKENS:
        if token in lowered:
            out.append(
                AuditFinding(
                    id="AUD-112",
                    severity=Severity.HIGH,
                    message=f"name contains reserved vendor token '{token}'.",
                    file=skill.path,
                    rule_kind="frontmatter",
                    field="name",
                    remediation=(
                        "Skill names must not embed vendor brand tokens "
                        "(anthropic / claude / openai / cursor / codex)."
                    ),
                    category="frontmatter",
                )
            )
            break

    return out


# ---------------------------------------------------------------------------
# Description rules — AUD-120..125
# ---------------------------------------------------------------------------


def _check_description(skill: SkillFile, fm: dict[str, object]) -> list[AuditFinding]:
    desc_raw = fm.get("description")
    if not isinstance(desc_raw, str) or not desc_raw.strip():
        return []
    desc = desc_raw.strip()
    out: list[AuditFinding] = []

    # AUD-120 max length.
    if len(desc) > DESCRIPTION_MAX_LEN:
        out.append(
            AuditFinding(
                id="AUD-120",
                severity=Severity.HIGH,
                message=(
                    f"description length {len(desc)} exceeds the spec maximum "
                    f"of {DESCRIPTION_MAX_LEN}."
                ),
                file=skill.path,
                rule_kind="description",
                field="description",
                remediation=(
                    f"Shorten the description; front-load the most important "
                    f"information in the first {DESCRIPTION_MAX_LEN} characters."
                ),
                category="description",
            )
        )

    # AUD-121 min length (low warn — Anthropic guideline ≥ 20 chars).
    if len(desc) < DESCRIPTION_MIN_LEN:
        out.append(
            AuditFinding(
                id="AUD-121",
                severity=Severity.LOW,
                message=(
                    f"description is too short ({len(desc)} chars; Anthropic "
                    f"recommends ≥ {DESCRIPTION_MIN_LEN})."
                ),
                file=skill.path,
                rule_kind="description",
                field="description",
                remediation="Explain what the skill does and when to load it.",
                category="description",
            )
        )

    # AUD-122 XML/HTML tags inside description.
    tags = _XML_TAG_RE.findall(desc)
    if tags:
        out.append(
            AuditFinding(
                id="AUD-122",
                severity=Severity.HIGH,
                message=f"description contains XML/HTML tags: {tags!r}.",
                file=skill.path,
                rule_kind="description",
                field="description",
                remediation="Remove markup tags from the description; use plain text.",
                category="description",
            )
        )

    # AUD-123 first-person voice.
    if _FIRST_PERSON_RE.search(desc):
        out.append(
            AuditFinding(
                id="AUD-123",
                severity=Severity.LOW,
                message="description uses first-person voice (I / My / I'm ...).",
                file=skill.path,
                rule_kind="description",
                field="description",
                remediation=(
                    "Use third-person, action-oriented phrasing such as "
                    "'Generates ...' or 'Analyzes ...'."
                ),
                category="description",
            )
        )

    # AUD-124 second-person voice.
    if _SECOND_PERSON_RE.search(desc):
        out.append(
            AuditFinding(
                id="AUD-124",
                severity=Severity.LOW,
                message="description uses second-person voice (You can / You should ...).",
                file=skill.path,
                rule_kind="description",
                field="description",
                remediation=(
                    "Use third-person, action-oriented phrasing such as "
                    "'Generates ...' or 'Analyzes ...'."
                ),
                category="description",
            )
        )

    # AUD-125 multi-line YAML block scalar (folded into a string with \n).
    # Note: PyYAML folds ``>-`` and ``|-`` block scalars into a single line at
    # parse time, so we only catch the case where the post-parse string still
    # contains an explicit ``\n``. A v0.2 enhancement is to retain the raw
    # frontmatter text and detect block-scalar indicators directly.
    if "\n" in desc:
        out.append(
            AuditFinding(
                id="AUD-125",
                severity=Severity.LOW,
                message=(
                    "description spans multiple lines (likely '|' or '>' YAML "
                    "block scalar). Single-line strings are the documented style."
                ),
                file=skill.path,
                rule_kind="description",
                field="description",
                remediation=(
                    "Rewrite the description as a single quoted line, e.g. "
                    'description: "Use when ..."'
                ),
                category="description",
            )
        )

    # AUD-126 missing trigger phrase (uses the 11-entry skilllint list).
    if not _has_trigger_phrase(desc):
        out.append(
            AuditFinding(
                id="AUD-126",
                severity=Severity.LOW,
                message=(
                    "description has no recognized trigger phrase "
                    "('use when' / 'use this' / 'when' / 'trigger' / ...)."
                ),
                file=skill.path,
                rule_kind="description",
                field="description",
                remediation=(
                    "Front-load a trigger clause like 'Use when …' so Claude "
                    "Code can decide when to auto-load the skill."
                ),
                category="description",
            )
        )

    return out


# ---------------------------------------------------------------------------
# Unknown / non-spec frontmatter field warning — AUD-130
# ---------------------------------------------------------------------------


def _check_unknown_fields(skill: SkillFile, fm: dict[str, object]) -> list[AuditFinding]:
    out: list[AuditFinding] = []
    for field in fm:
        if not isinstance(field, str):
            continue
        if field in _KNOWN_FRONTMATTER_FIELDS:
            continue
        out.append(
            AuditFinding(
                id="AUD-130",
                severity=Severity.LOW,
                message=(
                    f"unknown frontmatter field '{field}'; Anthropic spec "
                    "fields: name, description, version, author, source, "
                    "tags, allowed-tools, model, context, agent, hooks, "
                    "user-invocable, disable-model-invocation, skills."
                ),
                file=skill.path,
                rule_kind="frontmatter",
                field=field,
                remediation=(
                    "Drop the field, move it to the body, or document it as a vendor extension."
                ),
                category="frontmatter",
            )
        )
    return out


__all__ = [
    "DESCRIPTION_MAX_LEN",
    "DESCRIPTION_MIN_LEN",
    "NAME_MAX_LEN",
    "audit_naming",
]
