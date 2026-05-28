"""Audit: required frontmatter fields."""

from __future__ import annotations

from skillops_forge.models import AuditFinding, Severity, SkillFile, SkillFormat

# SKILL.md MUST declare these fields.
_SKILL_REQUIRED: tuple[str, ...] = ("name", "description")
# CLAUDE.md is free-form: only warn if no frontmatter at all.
_CLAUDE_RECOMMENDED: tuple[str, ...] = ("name",)


def audit_frontmatter(skill: SkillFile) -> list[AuditFinding]:
    """Verify required frontmatter fields are present.

    If the parser reported a YAML failure (``skill.parse_errors``), we emit a
    single CRITICAL finding and skip the per-field completeness checks — those
    would only produce noisy cascade errors against an already-broken file.
    """
    findings: list[AuditFinding] = []

    if skill.parse_errors:
        findings.append(
            AuditFinding(
                id="AUD-000",
                severity=Severity.CRITICAL,
                message=f"malformed YAML frontmatter: {skill.parse_errors[0]}",
                file=skill.path,
                rule_kind="frontmatter",
                field="<root>",
                remediation=(
                    "Quote the value, or use a YAML block scalar ('|' literal "
                    "or '>' folded) for multi-line strings. Example: "
                    "description: >-\\n  long text on\\n  multiple lines"
                ),
                category="frontmatter",
            )
        )
        return findings

    fm = skill.frontmatter or {}

    if skill.format == SkillFormat.SKILL_MD:
        if not fm:
            findings.append(
                AuditFinding(
                    id="AUD-001",
                    severity=Severity.HIGH,
                    message="SKILL.md is missing YAML frontmatter (--- block).",
                    file=skill.path,
                    rule_kind="frontmatter",
                    field="<root>",
                    remediation="Add a YAML frontmatter block with at least 'name' and 'description'.",
                    category="frontmatter",
                )
            )
        for field in _SKILL_REQUIRED:
            if not fm.get(field):
                findings.append(
                    AuditFinding(
                        id="AUD-002",
                        severity=Severity.HIGH,
                        message=f"frontmatter is missing required field '{field}'.",
                        file=skill.path,
                        rule_kind="frontmatter",
                        field=field,
                        remediation=f"Add '{field}: ...' to the YAML frontmatter.",
                        category="frontmatter",
                    )
                )
        # AUD-010 — recommend `version` for trust / changelog tracking.
        if not fm.get("version"):
            findings.append(
                AuditFinding(
                    id="AUD-010",
                    severity=Severity.LOW,
                    message=(
                        "Frontmatter is missing recommended field 'version' "
                        "for trust/changelog tracking."
                    ),
                    file=skill.path,
                    rule_kind="frontmatter",
                    field="version",
                    remediation="Add 'version: <semver>' to the YAML frontmatter.",
                    category="frontmatter",
                )
            )
        # AUD-011 — recommend at least one of `author` or `source` so the
        # source-trust hierarchy can be evaluated.
        if not (fm.get("author") or fm.get("source")):
            findings.append(
                AuditFinding(
                    id="AUD-011",
                    severity=Severity.LOW,
                    message=(
                        "Frontmatter lacks 'author' or 'source' — Source-Trust "
                        "hierarchy cannot be evaluated."
                    ),
                    file=skill.path,
                    rule_kind="frontmatter",
                    field="author|source",
                    remediation="Add 'author: <name>' or 'source: <url>' to the YAML frontmatter.",
                    category="frontmatter",
                )
            )

    elif skill.format == SkillFormat.CLAUDE_MD:
        if not fm:
            findings.append(
                AuditFinding(
                    id="AUD-003",
                    severity=Severity.LOW,
                    message="CLAUDE.md has no frontmatter (recommended for discovery).",
                    file=skill.path,
                    rule_kind="frontmatter",
                    field="<root>",
                    remediation="Consider adding a small frontmatter block with 'name'.",
                    category="frontmatter",
                )
            )
        else:
            for field in _CLAUDE_RECOMMENDED:
                if not fm.get(field):
                    findings.append(
                        AuditFinding(
                            id="AUD-003",
                            severity=Severity.LOW,
                            message=f"frontmatter is missing recommended field '{field}'.",
                            file=skill.path,
                            rule_kind="frontmatter",
                            field=field,
                            remediation=f"Add '{field}: ...' to the YAML frontmatter.",
                            category="frontmatter",
                        )
                    )
    return findings
