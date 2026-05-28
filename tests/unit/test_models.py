from __future__ import annotations

import json
from pathlib import Path

import pytest

from skillops_forge.models import (
    AuditFinding,
    Example,
    SecurityFinding,
    Severity,
    SkillFile,
    SkillFormat,
    SkillInventory,
    SkillReport,
)


def test_severity_values():
    assert Severity.CRITICAL.value == "critical"
    assert Severity.INFO.value == "info"


def test_skill_file_compute_sha256_is_stable():
    assert SkillFile.compute_sha256("a") == SkillFile.compute_sha256("a")
    assert SkillFile.compute_sha256("a") != SkillFile.compute_sha256("b")


def test_skill_file_section_lookup():
    skill = SkillFile(
        path=Path("SKILL.md"),
        format=SkillFormat.SKILL_MD,
        sections={"Inputs": "x", "Outputs": "y"},
    )
    assert skill.section("inputs") == "x"
    assert skill.section("OUTPUTS") == "y"
    assert skill.section("missing") == ""


def test_inventory_to_json_roundtrip():
    inv = SkillInventory(root=Path("."), files=())
    payload = json.loads(inv.to_json())
    assert payload["root"] == "."
    assert payload["files"] == []
    assert "scanned_at" in payload


def test_example_commands_coercion():
    ex = Example(commands=["echo hi"])
    assert ex.commands == ("echo hi",)


def test_audit_and_security_finding_to_dict():
    af = AuditFinding(
        id="AUD-001",
        severity=Severity.HIGH,
        message="m",
        file=Path("a.md"),
        line=1,
        rule_kind="frontmatter",
        field="name",
    )
    d = af.to_dict()
    assert d["severity"] == "high"
    assert d["file"] == "a.md"

    sf = SecurityFinding(
        id="SEC-001",
        rule_id="SEC-001",
        severity=Severity.CRITICAL,
        message="m",
        file=Path("b.md"),
        engine="regex",
    )
    sd = sf.to_dict()
    assert sd["rule_id"] == "SEC-001"
    assert sd["engine"] == "regex"


def test_skill_report_summary_and_json():
    inv = SkillInventory(root=Path("."), files=())
    rep = SkillReport(inventory=inv, score=90, threshold=70)
    assert rep.summary()["score"] == 90
    parsed = json.loads(rep.to_json())
    assert parsed["score"] == 90
    assert parsed["is_passed"] is True


def test_models_are_frozen():
    inv = SkillInventory(root=Path("."), files=())
    with pytest.raises(Exception):
        inv.tool_version = "x"  # type: ignore[misc]
