"""Audit: examples block completeness."""

from __future__ import annotations

from skillops_forge.models import AuditFinding, Severity, SkillFile, SkillFormat


def audit_examples(skill: SkillFile) -> list[AuditFinding]:
    """Warn if no examples are present in a SKILL.md."""
    findings: list[AuditFinding] = []
    if skill.format != SkillFormat.SKILL_MD:
        return findings
    if not skill.examples:
        findings.append(
            AuditFinding(
                id="AUD-040",
                severity=Severity.LOW,
                message="no fenced code-block examples were found.",
                file=skill.path,
                rule_kind="examples",
                field="<body>",
                remediation="Provide at least one fenced ```bash or ```python example.",
                category="examples",
            )
        )
    return findings
