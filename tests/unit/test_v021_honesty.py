"""Tests for v0.2.1 honesty release — dedup fix, SEC-018/019, AUD-013 silence."""

from __future__ import annotations

from pathlib import Path

from skillops_forge.parser import parse_path
from skillops_forge.scanner import ScannerEngine, run_scan


def _skill_with_body(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "SKILL.md"
    p.write_text(
        "---\nname: t\nversion: 0.1.0\nauthor: tester\n"
        "description: Use when running v0.2.1 honesty regression tests.\n"
        "---\n\n# T\n\n"
        f"{body}\n\n## Inputs\n- a\n## Outputs\n- b\n",
        encoding="utf-8",
    )
    return p


# ---------------------------------------------------------------------------
# P0-1 / P0-2 — dedup must collapse same-evidence-different-line duplicates
# ---------------------------------------------------------------------------


def test_dedup_collapses_body_and_examples_overlap(tmp_path: Path) -> None:
    """One literal `sudo` mention inside a fenced code block must produce
    a single SEC-006 finding, not one per target domain (body + examples).
    """
    body = "Use when verifying overlap. Example below.\n\n```bash\nsudo rm /tmp/x\n```\n"
    skill = _skill_with_body(tmp_path, body)
    inv = parse_path(skill)
    findings = run_scan(inv)
    sec006 = [f for f in findings if f.rule_id == "SEC-006"]
    # exactly one finding for the single sudo evidence
    assert len(sec006) == 1, f"got {len(sec006)} SEC-006 findings: {sec006}"


def test_frontmatter_target_emits_zero_line(tmp_path: Path) -> None:
    """Findings hitting the synthetic frontmatter / examples scan space
    must report (0, 0) for line/column — virtual offsets would mislead.
    """
    body = "Use when verifying overlap.\n\n```bash\nsudo rm /tmp/x\n```\n"
    skill = _skill_with_body(tmp_path, body)
    inv = parse_path(skill)
    eng = ScannerEngine.from_builtins()
    raw = eng.scan(inv.files[0])
    # The body match should have a real line; any examples / frontmatter hit
    # should report line == 0.
    body_hits = [f for f in raw if f.category == "body"]
    other_hits = [f for f in raw if f.category in {"frontmatter", "examples"}]
    for f in body_hits:
        assert f.line >= 1
    for f in other_hits:
        assert f.line == 0
        assert f.column == 0


# ---------------------------------------------------------------------------
# P1-1 — SEC-018 (reflective) + SEC-019 (string-concat) bypass coverage
# ---------------------------------------------------------------------------


def test_sec018_catches_getattr_builtins(tmp_path: Path) -> None:
    skill = _skill_with_body(tmp_path, 'getattr(__builtins__, "exec")(payload)')
    inv = parse_path(skill)
    ids = {f.rule_id for f in run_scan(inv)}
    assert "SEC-018" in ids


def test_sec018_catches_import_builtins_exec(tmp_path: Path) -> None:
    skill = _skill_with_body(tmp_path, 'm = __import__("builtins").exec; m(payload)')
    inv = parse_path(skill)
    ids = {f.rule_id for f in run_scan(inv)}
    assert "SEC-018" in ids


def test_sec018_catches_vars_builtins_dict_access(tmp_path: Path) -> None:
    skill = _skill_with_body(tmp_path, 'vars(__builtins__)["eval"](payload)')
    inv = parse_path(skill)
    ids = {f.rule_id for f in run_scan(inv)}
    assert "SEC-018" in ids


def test_sec019_catches_string_concat_eval(tmp_path: Path) -> None:
    skill = _skill_with_body(tmp_path, "y = 'ev' + 'al'; getattr(__builtins__, y)(payload)")
    inv = parse_path(skill)
    ids = {f.rule_id for f in run_scan(inv)}
    # Both rules should fire — concat name + reflective access.
    assert "SEC-019" in ids
    assert "SEC-018" in ids


def test_sec019_catches_compile_concat(tmp_path: Path) -> None:
    skill = _skill_with_body(
        tmp_path, "z = 'comp' + 'ile'; getattr(__builtins__, z)(payload, '<x>', 'eval')"
    )
    inv = parse_path(skill)
    ids = {f.rule_id for f in run_scan(inv)}
    assert "SEC-019" in ids


def test_sec019_does_not_misfire_on_innocent_concat(tmp_path: Path) -> None:
    """A plain literal concat that does not span an eval/exec/compile name
    should not trigger SEC-019.
    """
    skill = _skill_with_body(tmp_path, "greeting = 'hello' + ' world'")
    inv = parse_path(skill)
    ids = {f.rule_id for f in run_scan(inv)}
    assert "SEC-019" not in ids


# ---------------------------------------------------------------------------
# P1-2 — AUD-013 silence when AUD-121 already fires
# ---------------------------------------------------------------------------


def test_aud013_silent_when_aud121_fires(tmp_path: Path) -> None:
    """A description shorter than 20 chars triggers only AUD-121, not AUD-013."""
    from skillops_forge.auditor.description import audit_description
    from skillops_forge.auditor.naming import audit_naming

    p = tmp_path / "SKILL.md"
    p.write_text(
        "---\nname: t\nversion: 0.1.0\nauthor: tester\ndescription: Tiny\n---\n\n# T\n\n## Inputs\n- a\n## Outputs\n- b\n",
        encoding="utf-8",
    )
    inv = parse_path(p)
    desc_ids = {f.id for f in audit_description(inv.files[0])}
    naming_ids = {f.id for f in audit_naming(inv.files[0])}
    assert "AUD-121" in naming_ids
    assert "AUD-013" not in desc_ids


def test_aud013_still_fires_in_band_20_to_30(tmp_path: Path) -> None:
    """Descriptions in [20, 30) still get AUD-013 because AUD-121 is silent."""
    from skillops_forge.auditor.description import audit_description

    p = tmp_path / "SKILL.md"
    # 25 chars — between AUD-121 (<20) and the legacy 30-char floor.
    desc = "Use when verifying band"  # 23 chars
    assert 20 <= len(desc) < 30, f"description must be in [20, 30) for this test, got {len(desc)}"
    p.write_text(
        f"---\nname: t\nversion: 0.1.0\nauthor: tester\ndescription: {desc}\n---\n\n# T\n\n## Inputs\n- a\n## Outputs\n- b\n",
        encoding="utf-8",
    )
    inv = parse_path(p)
    desc_ids = {f.id for f in audit_description(inv.files[0])}
    assert "AUD-013" in desc_ids
