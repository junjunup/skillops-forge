"""Rule catalog — single source of truth for ``skillops rules`` / ``skillops rule``.

SEC rules are introspected at runtime from :class:`ScannerEngine.from_builtins`
(YAML data is the authoritative source).

AUD rules are static metadata — each rule lives inside a Python audit module,
so we maintain a hand-curated mirror here (kept in lockstep with the auditor
modules and the per-version CHANGELOG).
"""

from __future__ import annotations

from dataclasses import dataclass

from skillops_forge.config import docs_url_for
from skillops_forge.models import Severity
from skillops_forge.scanner import ScannerEngine


@dataclass(frozen=True, slots=True)
class RuleInfo:
    """A unified description of a rule (audit or security)."""

    id: str
    kind: str  # "audit" | "security"
    severity: Severity
    name: str
    message: str
    remediation: str
    docs_url: str

    @property
    def category(self) -> str:
        """Coarse grouping for display (frontmatter / sizing / scanner / …)."""
        if self.kind == "audit":
            head = self.id.split("-", 1)[1] if "-" in self.id else "0"
            try:
                bucket = int(head) // 100
            except ValueError:
                return "audit"
            return {
                0: "frontmatter",
                1: "naming",
                2: "permissions",
                3: "io_schema",
                4: "examples",
                # AUD-100..199 sizing, AUD-110..130 naming/desc — overflow into
                # bucket 1; we already returned "naming" above, so this is fine.
            }.get(bucket, "audit")
        return "security"


# ---------------------------------------------------------------------------
# Hand-curated AUD metadata (mirrors auditor/* modules).
# ---------------------------------------------------------------------------

_AUD_TABLE: tuple[tuple[str, Severity, str, str, str], ...] = (
    (
        "AUD-000",
        Severity.CRITICAL,
        "Malformed YAML frontmatter",
        "frontmatter could not be parsed as YAML",
        "Quote the value, or use a YAML block scalar ('|' literal or '>' folded) for multi-line strings.",
    ),
    (
        "AUD-001",
        Severity.HIGH,
        "Missing frontmatter block",
        "SKILL.md is missing the YAML frontmatter '---' delimiters",
        "Add a YAML frontmatter block with at least 'name' and 'description'.",
    ),
    (
        "AUD-002",
        Severity.HIGH,
        "Missing required frontmatter field",
        "frontmatter is missing 'name' or 'description'",
        "Add the missing field to the frontmatter.",
    ),
    (
        "AUD-003",
        Severity.LOW,
        "CLAUDE.md frontmatter recommended",
        "CLAUDE.md has no frontmatter / lacks recommended field",
        "Consider adding a small frontmatter block.",
    ),
    (
        "AUD-010",
        Severity.LOW,
        "Recommended field 'version' missing",
        "frontmatter lacks 'version' for trust/changelog tracking",
        "Add 'version: <semver>'.",
    ),
    (
        "AUD-011",
        Severity.LOW,
        "Recommended fields 'author' / 'source' missing",
        "frontmatter lacks 'author' or 'source' — Source-Trust hierarchy unavailable",
        "Add 'author: <name>' or 'source: <url>'.",
    ),
    (
        "AUD-013",
        Severity.LOW,
        "Description short for review",
        "description is shorter than 30 chars",
        "Add a sentence describing what the skill does and when to load it.",
    ),
    (
        "AUD-020",
        Severity.MEDIUM,
        "Shell example without allowed-tools",
        "body contains shell examples but 'allowed-tools' is empty",
        "Declare 'allowed-tools: [Bash]' or a tighter subset.",
    ),
    (
        "AUD-021",
        Severity.LOW,
        "Wildcard in allowed-tools",
        "'allowed-tools' uses a wildcard which over-permits the skill",
        "Replace wildcards with explicit tool names.",
    ),
    (
        "AUD-030",
        Severity.LOW,
        "Missing Inputs/Outputs sections",
        "no '## Inputs' / '## Outputs' headers found",
        "Document inputs and outputs as Markdown sections for reviewer clarity.",
    ),
    (
        "AUD-040",
        Severity.LOW,
        "Missing fenced examples",
        "no fenced code-block examples found",
        "Add at least one runnable fenced code block to demonstrate usage.",
    ),
    (
        "AUD-100",
        Severity.LOW,
        "Body line count exceeds budget",
        "body exceeds the recommended 500-line budget",
        "Split the skill into smaller skills, or move material into 'references/'.",
    ),
    (
        "AUD-101",
        Severity.LOW,
        "Body token estimate above warning threshold",
        "body token estimate ≥ 4400 (TOKEN_WARNING_THRESHOLD)",
        "Move supporting material into 'references/' to keep context-window cost in check.",
    ),
    (
        "AUD-102",
        Severity.HIGH,
        "Body token estimate above error threshold",
        "body token estimate ≥ 8800 (TOKEN_ERROR_THRESHOLD)",
        "Aggressively trim the body; offload long content to 'references/'.",
    ),
    (
        "AUD-110",
        Severity.HIGH,
        "Name not kebab-case",
        "name violates ^[a-z0-9]+(-[a-z0-9]+)*$",
        "Rename to lowercase kebab-case.",
    ),
    (
        "AUD-111",
        Severity.HIGH,
        "Name too long",
        "name length exceeds 64 characters",
        "Shorten the name to ≤ 64 characters.",
    ),
    (
        "AUD-112",
        Severity.HIGH,
        "Name uses reserved vendor token",
        "name embeds anthropic / claude / openai / cursor / codex",
        "Drop vendor brand tokens from the skill name.",
    ),
    (
        "AUD-120",
        Severity.HIGH,
        "Description exceeds 1024 chars",
        "description is too long",
        "Front-load critical info in the first 1024 characters.",
    ),
    (
        "AUD-121",
        Severity.LOW,
        "Description too short (<20 chars)",
        "Anthropic guideline minimum is 20 chars",
        "Explain what the skill does and when to load it.",
    ),
    (
        "AUD-122",
        Severity.HIGH,
        "Description contains XML/HTML tags",
        "description embeds markup tags",
        "Use plain text in the description.",
    ),
    (
        "AUD-123",
        Severity.LOW,
        "Description uses first-person voice",
        "description uses 'I / My / I will'",
        "Use third-person, action-oriented phrasing.",
    ),
    (
        "AUD-124",
        Severity.LOW,
        "Description uses second-person voice",
        "description uses 'You can / You should'",
        "Use third-person, action-oriented phrasing.",
    ),
    (
        "AUD-125",
        Severity.LOW,
        "Description spans multiple lines",
        "description uses a literal block scalar that retains newlines",
        "Rewrite as a single quoted line.",
    ),
    (
        "AUD-126",
        Severity.LOW,
        "Description missing trigger phrase",
        "description has no recognized trigger ('use when' / 'when' / 'trigger' / …)",
        "Front-load a trigger clause like 'Use when …'.",
    ),
    (
        "AUD-130",
        Severity.LOW,
        "Unknown frontmatter field",
        "field is not in the Anthropic spec whitelist",
        "Drop, move to body, or document as a vendor extension.",
    ),
    (
        "AUD-200",
        Severity.MEDIUM,
        "Broken internal Markdown link",
        "relative link points to a non-existent file",
        "Either create the missing file or correct the link target.",
    ),
    (
        "AUD-201",
        Severity.LOW,
        "Relative link missing './' prefix",
        "relative link omits the leading './'",
        "Prefix relative paths with './' for explicit relativity.",
    ),
    (
        "AUD-300",
        Severity.LOW,
        "Missing references/ directory",
        "skill directory has no 'references/' folder",
        "Add a 'references/' subdirectory for supporting documentation.",
    ),
    (
        "AUD-301",
        Severity.LOW,
        "Missing examples/ directory",
        "skill directory has no 'examples/' folder",
        "Add an 'examples/' subdirectory for runnable demos.",
    ),
    (
        "AUD-302",
        Severity.LOW,
        "Missing scripts/ directory",
        "skill directory has no 'scripts/' folder",
        "Add a 'scripts/' subdirectory for helper scripts.",
    ),
)


def _audit_rules() -> list[RuleInfo]:
    out: list[RuleInfo] = []
    for rid, severity, name, message, remediation in _AUD_TABLE:
        out.append(
            RuleInfo(
                id=rid,
                kind="audit",
                severity=severity,
                name=name,
                message=message,
                remediation=remediation,
                docs_url=docs_url_for(rid),
            )
        )
    return out


def _security_rules() -> list[RuleInfo]:
    engine = ScannerEngine.from_builtins()
    out: list[RuleInfo] = []
    for rule in engine.rules:
        out.append(
            RuleInfo(
                id=rule.id,
                kind="security",
                severity=rule.severity,
                name=rule.name,
                message=rule.message,
                remediation=rule.remediation,
                docs_url=docs_url_for(rule.id),
            )
        )
    return out


def list_rules() -> list[RuleInfo]:
    """Return all known rules (security first, then audit), sorted by ID."""
    rules = _security_rules() + _audit_rules()
    return sorted(rules, key=lambda r: (r.kind, r.id))


def get_rule(rule_id: str) -> RuleInfo | None:
    """Return a single rule by ID (case-insensitive)."""
    needle = rule_id.upper()
    for rule in list_rules():
        if rule.id.upper() == needle:
            return rule
    return None


__all__ = ["RuleInfo", "get_rule", "list_rules"]
