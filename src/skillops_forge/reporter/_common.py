"""Common Jinja2 context builder shared by Markdown and HTML reporters."""

from __future__ import annotations

from typing import Any

from skillops_forge.config import SEVERITY_COLORS
from skillops_forge.models import Severity, SkillReport

# RPT-B mapping (skill-vetter-style decision aid)
_RECOMMENDED_ACTION: dict[str, str] = {
    Severity.INFO.value: "Safe to install.",
    Severity.LOW.value: "Basic review, install OK.",
    Severity.MEDIUM.value: "Full code review required before install.",
    Severity.HIGH.value: "Human approval required; do not install without review.",
    Severity.CRITICAL.value: "DO NOT INSTALL. Address all critical findings first.",
}


def recommended_action(risk: Severity) -> str:
    """Return the human-readable recommended action for a risk level (RPT-B)."""
    return _RECOMMENDED_ACTION.get(risk.value, "Review the report before installing.")


def build_context(report: SkillReport) -> dict[str, Any]:
    """Return the dict of variables exposed to report templates."""
    summary = report.summary()
    findings_table: list[dict[str, Any]] = []
    for af in report.audit_findings:
        findings_table.append(
            {
                "kind": "audit",
                "id": af.id,
                "severity": af.severity.value,
                "color": SEVERITY_COLORS.get(af.severity.value, "#888"),
                "message": af.message,
                "file": str(af.file).replace("\\", "/"),
                "line": af.line,
                "remediation": af.remediation,
                "category": af.rule_kind or af.category,
            }
        )
    for sf in report.security_findings:
        findings_table.append(
            {
                "kind": "security",
                "id": sf.rule_id or sf.id,
                "severity": sf.severity.value,
                "color": SEVERITY_COLORS.get(sf.severity.value, "#888"),
                "message": sf.message,
                "file": str(sf.file).replace("\\", "/"),
                "line": sf.line,
                "remediation": sf.remediation,
                "category": sf.engine,
                "matched": sf.matched_text,
            }
        )
    inventory_rows = [
        {
            "path": str(s.path).replace("\\", "/"),
            "format": s.format.value,
            "sha": s.sha256[:10],
            "lines": s.line_count,
            "examples": len(s.examples),
        }
        for s in report.inventory.files
    ]
    examples_rows = [
        {
            "title": run.example_title,
            "file": str(run.file).replace("\\", "/"),
            "success": run.success,
            "blocked": [
                {"severity": b.severity.value, "message": b.message} for b in run.blocked_actions
            ],
        }
        for run in report.example_runs
    ]

    # RPT-A: surface the permission summary even when None so templates have a
    # stable shape.
    perm = report.permission_summary
    permission_rows = {
        "files_read": list(perm.files_read) if perm else [],
        "files_write": list(perm.files_write) if perm else [],
        "commands": list(perm.commands) if perm else [],
        "network": list(perm.network) if perm else [],
        "is_empty": perm.is_empty() if perm else True,
    }

    # RPT-C: ⚠️ CAUTION middle-state — passed by score+threshold, but a HIGH
    # finding is present (no CRITICAL — that path stays "FAILED").
    high_finding_count = sum(
        1
        for f in (*report.audit_findings, *report.security_findings)
        if f.severity == Severity.HIGH
    )
    show_caution = bool(report.is_passed and high_finding_count > 0)

    target_path = (
        str(report.target).replace("\\", "/")
        if report.target is not None
        else str(report.inventory.root).replace("\\", "/")
    )

    return {
        "report": report,
        "summary": summary,
        "score_color": SEVERITY_COLORS.get(report.overall_risk.value, "#5C8DB7"),
        "severity_colors": SEVERITY_COLORS,
        "findings_table": findings_table,
        "inventory_rows": inventory_rows,
        "examples_rows": examples_rows,
        "permission_rows": permission_rows,
        "recommended_action": recommended_action(report.overall_risk),
        "show_caution": show_caution,
        "high_finding_count": high_finding_count,
        "tool_version": report.tool_version,
        "generated_at": report.generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target_path": target_path,
    }


__all__ = ["build_context", "recommended_action"]
