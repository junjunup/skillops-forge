"""Audit: input/output contract presence."""

from __future__ import annotations

from skillops_forge.models import AuditFinding, Severity, SkillFile, SkillFormat

_INPUT_HEADINGS: tuple[str, ...] = ("Inputs", "Input", "Parameters", "Arguments")
_OUTPUT_HEADINGS: tuple[str, ...] = ("Outputs", "Output", "Returns", "Result")


def audit_io_schema(skill: SkillFile) -> list[AuditFinding]:
    """Warn when neither input nor output contract is documented."""
    findings: list[AuditFinding] = []
    if skill.format == SkillFormat.CURSOR_RULES:
        return findings  # rules tend to be free-form
    has_input = any(skill.section(h) for h in _INPUT_HEADINGS)
    has_output = any(skill.section(h) for h in _OUTPUT_HEADINGS)
    if not has_input and not has_output and skill.format == SkillFormat.SKILL_MD:
        findings.append(
            AuditFinding(
                id="AUD-030",
                severity=Severity.LOW,
                message="no Input/Output sections documented.",
                file=skill.path,
                rule_kind="io",
                field="<sections>",
                remediation="Add '## Inputs' and '## Outputs' sections.",
                category="io_schema",
            )
        )
    return findings
