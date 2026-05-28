"""Pipeline orchestration: parser → audit → scan → run → score → report."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from skillops_forge import __version__
from skillops_forge.auditor import run_audit
from skillops_forge.auditor.permission_summary import extract_permission_summary
from skillops_forge.config import DEFAULT_THRESHOLD, docs_url_for
from skillops_forge.logging_setup import get_logger
from skillops_forge.models import (
    AuditFinding,
    Finding,
    SecurityFinding,
    SkillReport,
)
from skillops_forge.parser import parse_path
from skillops_forge.plugins.protocol import PluginProtocol
from skillops_forge.reporter.scoring import calculate_score
from skillops_forge.runner import run_examples
from skillops_forge.scanner import run_scan

logger = get_logger()

_F = TypeVar("_F", bound=Finding)


def run_pipeline(
    target: Path,
    *,
    threshold: int = DEFAULT_THRESHOLD,
    include_cursor_rules: bool = True,
    enable_runner: bool = True,
    plugins: list[PluginProtocol] | None = None,
) -> SkillReport:
    """Run the full SkillOps Forge pipeline against ``target``.

    Args:
        target: Path to a directory or a single skill file.
        threshold: Minimum acceptable score; below this the run is marked failed.
        include_cursor_rules: Whether to descend into ``.cursor/rules`` trees.
        enable_runner: When False, the examples dry-run stage is skipped.
        plugins: Optional list of :class:`PluginProtocol` instances (P1).

    Returns:
        A fully populated :class:`SkillReport`. The ``is_passed`` verdict is a
        computed pydantic field on the report itself (one-strike CRITICAL veto
        + score threshold).
    """
    target = Path(target)
    plugins = plugins or []

    logger.info("scanning target: %s", target)
    inventory = parse_path(target, include_cursor_rules=include_cursor_rules)
    logger.info("found %d skill file(s)", len(inventory.files))
    for plugin in plugins:
        plugin.on_inventory(inventory)

    audit_findings: list[AuditFinding] = run_audit(inventory)
    audit_findings = [_enrich_finding(f) for f in audit_findings]
    logger.info("audit findings: %d", len(audit_findings))

    permission_summary = extract_permission_summary(inventory)
    logger.info(
        "permission summary: read=%d write=%d cmd=%d net=%d",
        len(permission_summary.files_read),
        len(permission_summary.files_write),
        len(permission_summary.commands),
        len(permission_summary.network),
    )

    security_findings: list[SecurityFinding] = run_scan(inventory)
    security_findings = [_enrich_finding(f) for f in security_findings]
    logger.info("security findings: %d", len(security_findings))

    example_runs = run_examples(inventory) if enable_runner else []
    logger.info("examples dry-run: %d", len(example_runs))

    runner_findings: list[SecurityFinding] = []
    for run in example_runs:
        runner_findings.extend(_enrich_finding(f) for f in run.blocked_actions)

    all_findings: list[Finding] = []
    all_findings.extend(audit_findings)
    all_findings.extend(security_findings)
    all_findings.extend(runner_findings)

    # Plugin hook: post-findings transformation.
    for plugin in plugins:
        transformed = plugin.on_findings(all_findings)
        if transformed is not None:
            all_findings = list(transformed)

    score, overall_risk = calculate_score(all_findings)

    report = SkillReport(
        inventory=inventory,
        audit_findings=tuple(audit_findings),
        security_findings=tuple(security_findings),
        example_runs=tuple(example_runs),
        score=score,
        overall_risk=overall_risk,
        threshold=threshold,
        tool_version=__version__,
        target=target,
        permission_summary=permission_summary,
    )
    for plugin in plugins:
        replacement = plugin.on_report(report)
        if replacement is not None:
            report = replacement
    return report


__all__ = ["run_pipeline"]


def _enrich_finding(finding: _F) -> _F:
    """Populate ``docs_url`` and ``suggestion`` when missing.

    SkillOps Forge keeps rule-side authoring lightweight: rules only emit
    ``message`` + ``remediation``. The pipeline derives:

    * ``docs_url`` — canonical per-rule docs path (config.docs_url_for).
    * ``suggestion`` — first sentence of ``remediation`` so terse CLI/HTML
      output has an actionable line without showing the full remediation
      paragraph. Rules that already populate ``suggestion`` are preserved.
    """
    updates: dict[str, str] = {}
    if not finding.docs_url:
        rule_key = ""
        rule_id_attr = getattr(finding, "rule_id", "")
        if isinstance(rule_id_attr, str) and rule_id_attr:
            rule_key = rule_id_attr
        elif finding.id:
            rule_key = finding.id
        if rule_key:
            updates["docs_url"] = docs_url_for(rule_key)
    if not finding.suggestion and finding.remediation:
        # Take the first sentence (split on '. ' / '! ' / '? '), capped at 180 chars.
        first = finding.remediation.split(". ", 1)[0].strip()
        if len(first) > 180:
            first = first[:177].rstrip() + "..."
        updates["suggestion"] = first
    if not updates:
        return finding
    return finding.model_copy(update=updates)
