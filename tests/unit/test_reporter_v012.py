"""Tests for v0.1.2 reporter additions: target field (FIX-1), permission summary
(RPT-A), recommended action (RPT-B), and the ⚠️ CAUTION middle-state (RPT-C)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skillops_forge.auditor.permission_summary import extract_permission_summary
from skillops_forge.models import (
    AuditFinding,
    PermissionSummary,
    SecurityFinding,
    Severity,
    SkillInventory,
    SkillReport,
)
from skillops_forge.parser import parse_path
from skillops_forge.pipeline import run_pipeline
from skillops_forge.reporter import render
from skillops_forge.reporter._common import recommended_action

# ---------------------------------------------------------------------------
# FIX-1: SkillReport.target survives serialization as POSIX string
# ---------------------------------------------------------------------------


def test_fix1_target_field_present_in_json(good_root: Path) -> None:
    target = good_root / "skill-md-basic"
    report = run_pipeline(target)
    assert report.target == target
    payload = json.loads(report.model_dump_json())
    assert payload["target"] is not None
    assert "skill-md-basic" in payload["target"]
    # Always POSIX, never raw Windows backslashes.
    assert "\\" not in payload["target"]


def test_fix1_target_none_when_no_target(tmp_path: Path) -> None:
    rep = SkillReport(inventory=SkillInventory(root=tmp_path, files=()))
    payload = json.loads(rep.model_dump_json())
    assert payload["target"] is None


# ---------------------------------------------------------------------------
# RPT-A: PermissionSummary extractor + serialization
# ---------------------------------------------------------------------------


def test_rpta_permission_summary_populated_for_good_fixture(good_root: Path) -> None:
    inv = parse_path(good_root / "skill-md-with-examples")
    summary = extract_permission_summary(inv)
    # Expected: at least Python's read_text (read), commands like python.
    assert "python" in summary.commands
    # Should not be entirely empty.
    assert not summary.is_empty()


def test_rpta_permission_summary_extracts_read_write_paths(tmp_path: Path) -> None:
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text(
        "---\n"
        "name: rwsamp\n"
        "description: Use this skill when the body contains an explicit cat-then-tee pattern for testing the permission extractor.\n"
        "version: 0.1.0\n"
        "author: tester\n"
        "---\n"
        "# Body\n"
        "## Inputs\nfoo\n\n## Outputs\nbar\n\n"
        "```bash\n"
        "cat ./input.json\n"
        "echo done > /tmp/out.log\n"
        "curl https://example.org/api\n"
        "```\n",
        encoding="utf-8",
    )
    summary = extract_permission_summary(parse_path(tmp_path))
    assert any("input.json" in p for p in summary.files_read)
    assert any("out.log" in p for p in summary.files_write)
    assert "cat" in summary.commands
    assert "curl" in summary.commands
    assert any("example.org" in u for u in summary.network)


def test_rpta_pipeline_includes_permission_summary(good_root: Path) -> None:
    report = run_pipeline(good_root / "skill-md-with-examples")
    assert isinstance(report.permission_summary, PermissionSummary)
    payload = json.loads(report.model_dump_json())
    assert "permission_summary" in payload
    perm = payload["permission_summary"]
    assert isinstance(perm, dict)
    for key in ("files_read", "files_write", "commands", "network"):
        assert key in perm
        assert isinstance(perm[key], list)


def test_rpta_permission_summary_handles_broken_frontmatter(tmp_path: Path) -> None:
    """The extractor must never raise when frontmatter is malformed."""
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text(
        "---\n"
        "name: broken\n"
        "description: Has a colon in: the multi-line continuation.\n"
        "    second: line breaks the parser.\n"
        "---\n"
        "## Inputs\nx\n",
        encoding="utf-8",
    )
    inv = parse_path(tmp_path)
    summary = extract_permission_summary(inv)
    # Should not raise; may even be empty.
    assert isinstance(summary, PermissionSummary)


# ---------------------------------------------------------------------------
# RPT-B: Recommended Action mapping + template rendering
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "risk, snippet",
    [
        (Severity.INFO, "Safe to install."),
        (Severity.LOW, "Basic review"),
        (Severity.MEDIUM, "Full code review"),
        (Severity.HIGH, "Human approval required"),
        (Severity.CRITICAL, "DO NOT INSTALL"),
    ],
)
def test_rptb_recommended_action_text(risk: Severity, snippet: str) -> None:
    text = recommended_action(risk)
    assert snippet in text


def test_rptb_md_report_contains_recommended_action(good_root: Path, tmp_path: Path) -> None:
    report = run_pipeline(good_root / "skill-md-basic")
    written = render(report, fmt="md", out_dir=tmp_path)
    md = written[0].read_text(encoding="utf-8")
    assert "**Recommended Action**" in md


def test_rptb_html_report_contains_recommended_action(good_root: Path, tmp_path: Path) -> None:
    report = run_pipeline(good_root / "skill-md-basic")
    written = render(report, fmt="html", out_dir=tmp_path)
    html = written[0].read_text(encoding="utf-8")
    assert "Recommended Action:" in html


# ---------------------------------------------------------------------------
# RPT-C: ⚠️ CAUTION middle state when score>=threshold but HIGH finding present
# ---------------------------------------------------------------------------


def _report_with_one_high(score: int = 85, threshold: int = 70) -> SkillReport:
    inv = SkillInventory(root=Path("."), files=())
    return SkillReport(
        inventory=inv,
        score=score,
        threshold=threshold,
        overall_risk=Severity.HIGH,
        security_findings=(
            SecurityFinding(
                id="SEC-006",
                rule_id="SEC-006",
                severity=Severity.HIGH,
                message="sudo detected",
                file=Path("a.md"),
            ),
        ),
    )


def test_rptc_caution_html_pill_when_passed_with_high(tmp_path: Path) -> None:
    rep = _report_with_one_high()
    assert rep.is_passed is True  # passed by score
    written = render(rep, fmt="html", out_dir=tmp_path)
    html = written[0].read_text(encoding="utf-8")
    assert 'class="pill caution"' in html
    assert "⚠️ CAUTION" in html


def test_rptc_caution_md_phrasing_when_passed_with_high(tmp_path: Path) -> None:
    rep = _report_with_one_high()
    written = render(rep, fmt="md", out_dir=tmp_path)
    md = written[0].read_text(encoding="utf-8")
    assert "PASSED WITH CAUTION" in md
    assert "⚠️ **CAUTION**" in md


def test_rptc_no_caution_when_passed_clean(good_root: Path, tmp_path: Path) -> None:
    rep = run_pipeline(good_root / "skill-md-basic")
    assert rep.is_passed is True
    written = render(rep, fmt="html", out_dir=tmp_path)
    html = written[0].read_text(encoding="utf-8")
    assert "pill caution" not in html


def test_rptc_no_caution_when_failed(bad_root: Path, tmp_path: Path) -> None:
    """A FAILED report must not display the CAUTION pill — failure stays failure."""
    rep = run_pipeline(bad_root / "curl-pipe-bash")
    assert rep.is_passed is False
    written = render(rep, fmt="html", out_dir=tmp_path)
    html = written[0].read_text(encoding="utf-8")
    assert "pill caution" not in html


# Reporter __init__ helper used implicitly in the tests above is
# `from skillops_forge.reporter import render`. Imported in module namespace
# so static analyzers don't flag it.
_ = AuditFinding  # type: ignore[misc]  # silence unused import warning
