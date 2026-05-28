"""Audit: progressive disclosure directory recommendations (PD series).

Inspired by skilllint PD001-PD003. The Anthropic skill format encourages
splitting supporting material into three optional subdirectories:

* ``references/`` — supporting documentation, citations, deep dives
* ``examples/``   — runnable demos
* ``scripts/``    — helper scripts the skill body invokes

These subdirectories only become meaningful once a skill is large enough
that its body benefits from offloading material. Real-world data showed
that emitting findings on **every** SKILL.md drowned simple single-file
skills in noise (87 hits across 37 user skills, almost all false
positives). We now gate the recommendation on a body-size threshold so the
audit fires only when splitting actually helps.
"""

from __future__ import annotations

from skillops_forge.models import AuditFinding, Severity, SkillFile, SkillFormat

# Body line count above which progressive-disclosure recommendations apply.
# Below this, the skill is small enough that a single file is fine.
_DISCLOSURE_LINE_THRESHOLD: int = 200

_DISCLOSURE_DIRS: tuple[tuple[str, str, str], ...] = (
    ("references", "AUD-300", "supporting documentation"),
    ("examples", "AUD-301", "runnable demos"),
    ("scripts", "AUD-302", "helper scripts"),
)


def audit_disclosure(skill: SkillFile) -> list[AuditFinding]:
    """Return findings for missing progressive-disclosure subdirectories.

    Only emits when:
      * the file is named ``SKILL.md`` (lives in a dedicated skill dir), and
      * the body has more than ``_DISCLOSURE_LINE_THRESHOLD`` lines — small
        skills don't need extra directories.
    """
    findings: list[AuditFinding] = []
    if skill.format != SkillFormat.SKILL_MD:
        return findings
    if skill.path.name.lower() != "skill.md":
        return findings  # only check files literally named SKILL.md
    body_line_count = (skill.body or "").count("\n") + (1 if skill.body else 0)
    if body_line_count <= _DISCLOSURE_LINE_THRESHOLD:
        return findings  # too small to benefit from splitting
    parent = skill.path.parent
    for dirname, rule_id, purpose in _DISCLOSURE_DIRS:
        candidate = parent / dirname
        if candidate.is_dir() and any(candidate.iterdir()):
            # treat empty dirs as "missing" — empty-dir gaming should not
            # count as compliance with the recommendation
            continue
        findings.append(
            AuditFinding(
                id=rule_id,
                severity=Severity.LOW,
                message=(
                    f"large skill ({body_line_count} body lines) has no "
                    f"non-empty '{dirname}/' subdirectory."
                ),
                file=skill.path,
                rule_kind="disclosure",
                field=dirname,
                remediation=(
                    f"Add a non-empty '{dirname}/' subdirectory for {purpose}; "
                    "this keeps the SKILL.md body lean and matches the "
                    "progressive-disclosure pattern."
                ),
                category="disclosure",
            )
        )
    return findings


__all__ = ["audit_disclosure"]
