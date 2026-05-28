from __future__ import annotations

import json
from pathlib import Path

from skillops_forge.models import (
    AuditFinding,
    Finding,
    SecurityFinding,
    Severity,
    SkillInventory,
    SkillReport,
)
from skillops_forge.reporter.scoring import calculate_score, is_passed


def _af(sev: Severity) -> AuditFinding:
    return AuditFinding(id="AUD", severity=sev, message="m", file=Path("a.md"))


def _sf(sev: Severity) -> SecurityFinding:
    return SecurityFinding(id="SEC", rule_id="SEC", severity=sev, message="m", file=Path("a.md"))


def test_score_no_findings():
    score, risk = calculate_score([])
    assert score == 100
    assert risk == Severity.INFO


def test_score_one_critical():
    findings: list[Finding] = [_sf(Severity.CRITICAL)]
    score, risk = calculate_score(findings)
    assert score == 75
    assert risk == Severity.CRITICAL


def test_score_three_high():
    findings: list[Finding] = [_sf(Severity.HIGH)] * 3
    score, risk = calculate_score(findings)
    assert score == 64
    assert risk == Severity.HIGH


def test_score_one_medium():
    findings: list[Finding] = [_af(Severity.MEDIUM)]
    score, risk = calculate_score(findings)
    assert score == 95
    assert risk == Severity.LOW


def test_is_passed_threshold_logic():
    assert is_passed(80, 70, has_critical=False) is True
    assert is_passed(60, 70, has_critical=False) is False
    assert is_passed(99, 70, has_critical=True) is False


def test_score_clamped_to_zero():
    findings: list[Finding] = [_sf(Severity.CRITICAL)] * 10
    score, _ = calculate_score(findings)
    assert score == 0


# ---------------------------------------------------------------------------
# is_passed as a computed field on SkillReport (P0 #2 regression coverage)
# ---------------------------------------------------------------------------


def _empty_inventory() -> SkillInventory:
    return SkillInventory(root=Path("."), files=())


def test_is_passed_computed_in_report_true_path():
    rep = SkillReport(inventory=_empty_inventory(), score=100, threshold=70)
    assert rep.is_passed is True


def test_is_passed_computed_in_report_below_threshold():
    rep = SkillReport(inventory=_empty_inventory(), score=50, threshold=70)
    assert rep.is_passed is False


def test_is_passed_computed_in_report_critical_security_veto():
    rep = SkillReport(
        inventory=_empty_inventory(),
        score=85,
        threshold=70,
        security_findings=(
            SecurityFinding(
                id="SEC-001",
                rule_id="SEC-001",
                severity=Severity.CRITICAL,
                message="curl|bash",
                file=Path("a.md"),
            ),
        ),
    )
    assert rep.is_passed is False


def test_is_passed_computed_in_report_critical_audit_veto():
    rep = SkillReport(
        inventory=_empty_inventory(),
        score=100,
        threshold=70,
        audit_findings=(
            AuditFinding(
                id="AUD-000",
                severity=Severity.CRITICAL,
                message="malformed YAML frontmatter",
                file=Path("a.md"),
                rule_kind="frontmatter",
                category="frontmatter",
            ),
        ),
    )
    assert rep.is_passed is False


def test_is_passed_computed_in_report_serializes_to_json():
    rep = SkillReport(inventory=_empty_inventory(), score=90, threshold=70)
    payload = json.loads(rep.model_dump_json())
    assert "is_passed" in payload
    assert isinstance(payload["is_passed"], bool)
    assert payload["is_passed"] is True
    # Legacy ``passed`` field must NOT leak into the schema any more.
    assert "passed" not in payload
