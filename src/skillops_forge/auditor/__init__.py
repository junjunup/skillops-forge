"""Structural auditor — runs every audit sub-module and aggregates findings."""

from __future__ import annotations

from skillops_forge.auditor.description import audit_description
from skillops_forge.auditor.disclosure import audit_disclosure
from skillops_forge.auditor.examples import audit_examples
from skillops_forge.auditor.frontmatter import audit_frontmatter
from skillops_forge.auditor.io_schema import audit_io_schema
from skillops_forge.auditor.links import audit_links
from skillops_forge.auditor.naming import audit_naming
from skillops_forge.auditor.permissions import audit_permissions
from skillops_forge.auditor.sizing import audit_sizing
from skillops_forge.models import AuditFinding, SkillInventory


def run_audit(inventory: SkillInventory) -> list[AuditFinding]:
    """Run all audit checks against every file in ``inventory``.

    When a file has ``parse_errors`` (malformed YAML frontmatter), only the
    frontmatter audit runs — all other downstream checks would cascade into
    noisy false-positives against an already-broken file. The frontmatter
    audit itself emits a single CRITICAL finding in that case.

    Returns a flat list of :class:`AuditFinding` entries (possibly empty).
    """
    findings: list[AuditFinding] = []
    for skill in inventory.files:
        findings.extend(audit_frontmatter(skill))
        if skill.parse_errors:
            continue
        findings.extend(audit_naming(skill))
        findings.extend(audit_description(skill))
        findings.extend(audit_permissions(skill))
        findings.extend(audit_io_schema(skill))
        findings.extend(audit_examples(skill))
        findings.extend(audit_sizing(skill))
        findings.extend(audit_links(skill))
        findings.extend(audit_disclosure(skill))
    return findings


__all__ = ["run_audit"]
