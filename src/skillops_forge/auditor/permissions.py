"""Audit: ``allowed-tools`` / permission declarations."""

from __future__ import annotations

import re

from skillops_forge.models import AuditFinding, Severity, SkillFile, SkillFormat

# Heuristics: if the body mentions one of these, we expect a matching tool.
_TOOL_HINTS: dict[str, tuple[str, ...]] = {
    "Bash": ("```bash", "```sh", "```shell", "```zsh"),
    "Read": ("read the file", "open the file"),
    "Write": ("write to", "create a file", "Write the file"),
    "Edit": ("edit the file", "modify the file"),
}
_BANNED = re.compile(r"\b(\*|all|any|.*?\*.*?)\b")


def audit_permissions(skill: SkillFile) -> list[AuditFinding]:
    """Verify declared ``allowed-tools`` are sane and not over-broad."""
    findings: list[AuditFinding] = []
    if skill.format != SkillFormat.SKILL_MD:
        return findings
    declared = list(skill.allowed_tools)
    body_lower = skill.body.lower()

    if not declared:
        # If body clearly invokes shell, this is at least MEDIUM.
        if any(hint in body_lower for hint in ("```bash", "```sh", "```shell", "```zsh")):
            findings.append(
                AuditFinding(
                    id="AUD-020",
                    severity=Severity.MEDIUM,
                    message="body contains shell examples but 'allowed-tools' is empty.",
                    file=skill.path,
                    rule_kind="permissions",
                    field="allowed-tools",
                    remediation="Declare 'allowed-tools: [Bash]' (or the minimum needed).",
                    category="permissions",
                )
            )
        return findings

    for tool in declared:
        if _BANNED.fullmatch(tool.strip()) and tool.strip() in {"*", "all", "any"}:
            findings.append(
                AuditFinding(
                    id="AUD-021",
                    severity=Severity.HIGH,
                    message=f"'allowed-tools' uses overly-broad value '{tool}'.",
                    file=skill.path,
                    rule_kind="permissions",
                    field="allowed-tools",
                    remediation="Replace wildcards with an explicit list of tool names.",
                    category="permissions",
                )
            )
    return findings
