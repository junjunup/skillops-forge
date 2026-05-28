from __future__ import annotations

from pathlib import Path

from skillops_forge.auditor import run_audit
from skillops_forge.parser import parse_path


def test_audit_good_inventory_has_no_findings(good_root: Path):
    inv = parse_path(good_root / "skill-md-basic")
    findings = run_audit(inv)
    assert findings == []


def test_audit_missing_frontmatter(bad_root: Path):
    inv = parse_path(bad_root / "missing-frontmatter")
    findings = run_audit(inv)
    assert any(f.rule_kind == "frontmatter" for f in findings)
    # Permissions audit should also fire because body has bash without allowed-tools.
    assert any(f.rule_kind == "permissions" for f in findings)


def test_audit_description_short(tmp_path: Path):
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text(
        "---\nname: short\ndescription: tiny\n---\n# body\n```bash\necho hi\n```\n",
        encoding="utf-8",
    )
    inv = parse_path(tmp_path)
    findings = run_audit(inv)
    assert any(f.rule_kind == "description" for f in findings)


def test_aud010_recommends_version_field(tmp_path: Path):
    """SKILL.md without 'version' should emit a single AUD-010 (low)."""
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text(
        "---\n"
        "name: noversion\n"
        "description: Use this skill when a SKILL.md is missing the recommended version field.\n"
        "author: someone\n"
        "---\n"
        "# body\n## Inputs\nx\n## Outputs\ny\n```bash\necho hi\n```\n",
        encoding="utf-8",
    )
    findings = run_audit(parse_path(tmp_path))
    aud010 = [f for f in findings if f.id == "AUD-010"]
    assert len(aud010) == 1
    assert aud010[0].severity.value == "low"
    assert aud010[0].field == "version"
    # AUD-011 must NOT fire because author is present.
    assert all(f.id != "AUD-011" for f in findings)


def test_aud011_recommends_author_or_source(tmp_path: Path):
    """SKILL.md without 'author' AND without 'source' should emit AUD-011 (low)."""
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text(
        "---\n"
        "name: noauthor\n"
        "description: Use this skill when a SKILL.md is missing both author and source fields.\n"
        "version: 0.1.0\n"
        "---\n"
        "# body\n## Inputs\nx\n## Outputs\ny\n```bash\necho hi\n```\n",
        encoding="utf-8",
    )
    findings = run_audit(parse_path(tmp_path))
    aud011 = [f for f in findings if f.id == "AUD-011"]
    assert len(aud011) == 1
    assert aud011[0].severity.value == "low"
    # AUD-010 must NOT fire because version is present.
    assert all(f.id != "AUD-010" for f in findings)


def test_aud011_satisfied_by_source_alone(tmp_path: Path):
    """Either 'author' or 'source' is enough — having only 'source' suppresses AUD-011."""
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text(
        "---\n"
        "name: source-only\n"
        "description: Use this skill when only the source url is set; author is omitted.\n"
        "version: 0.1.0\n"
        "source: https://example.org/skills/x\n"
        "---\n"
        "# body\n## Inputs\nx\n## Outputs\ny\n```bash\necho hi\n```\n",
        encoding="utf-8",
    )
    findings = run_audit(parse_path(tmp_path))
    assert all(f.id != "AUD-011" for f in findings)
