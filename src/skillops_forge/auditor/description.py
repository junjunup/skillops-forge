"""Audit: description quality (legacy length / trigger checks).

These checks are kept for backward compatibility. From v0.1.4 onwards the
stricter Anthropic-aligned naming/description rules live in
:mod:`skillops_forge.auditor.naming` (AUD-110..130).

To avoid double-scoring the same problem, AUD-013 is suppressed whenever the
new AUD-121 rule (description < 20 chars) would already fire on the same
text. It only emits when description is in [20, 30) chars — the band where
AUD-121 is silent but reviewers still benefit from a friendly nudge.
"""

from __future__ import annotations

from skillops_forge.auditor.naming import DESCRIPTION_MIN_LEN
from skillops_forge.models import AuditFinding, Severity, SkillFile, SkillFormat

_LEGACY_MIN_LEN = 30


def audit_description(skill: SkillFile) -> list[AuditFinding]:
    """Emit the legacy AUD-013 warning ONLY for descriptions in [20, 30) chars.

    Anything shorter (< 20) is already covered by AUD-121 in the naming
    auditor. Re-emitting AUD-013 there would produce a duplicate finding for
    the same defect, distorting the score and the report's signal/noise ratio.
    """
    findings: list[AuditFinding] = []
    if skill.format != SkillFormat.SKILL_MD:
        return findings
    description = str((skill.frontmatter or {}).get("description") or "").strip()
    if not description:
        return findings
    desc_len = len(description)
    # AUD-121 already covers the < DESCRIPTION_MIN_LEN range — stay silent there.
    if desc_len < DESCRIPTION_MIN_LEN:
        return findings
    if desc_len < _LEGACY_MIN_LEN:
        findings.append(
            AuditFinding(
                id="AUD-013",
                severity=Severity.LOW,
                message=(
                    f"description is short for review purposes "
                    f"({desc_len} chars; reviewers prefer ≥ {_LEGACY_MIN_LEN})."
                ),
                file=skill.path,
                rule_kind="description",
                field="description",
                remediation=("Add a sentence describing what the skill does and when to load it."),
                category="description",
            )
        )
    return findings
