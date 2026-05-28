from __future__ import annotations

from pathlib import Path

import pytest

from skillops_forge.parser import parse_path
from skillops_forge.scanner import ScannerEngine, run_scan


def test_engine_loads_at_least_eleven_rules():
    engine = ScannerEngine.from_builtins()
    # v0.1.2 added 6 new rules (SEC-012..017) on top of the 11 P0 rules.
    assert len(engine.rules) >= 17
    # ids are unique
    ids = [r.id for r in engine.rules]
    assert len(ids) == len(set(ids))
    # the new rule IDs must all be present
    for rid in ("SEC-012", "SEC-013", "SEC-014", "SEC-015", "SEC-016", "SEC-017"):
        assert rid in ids, f"missing rule {rid}"


@pytest.mark.parametrize(
    "fixture, expected_rule",
    [
        ("curl-pipe-bash", "SEC-001"),
        ("sensitive-path-aws", "SEC-003"),
        ("hidden-zerowidth", "SEC-007"),
        ("rm-rf-root", "SEC-005"),
        ("base64-blob", "SEC-008"),
    ],
)
def test_bad_fixture_triggers_expected_rule(bad_root: Path, fixture: str, expected_rule: str):
    inv = parse_path(bad_root / fixture)
    findings = run_scan(inv)
    rule_ids = {f.rule_id for f in findings}
    assert expected_rule in rule_ids, f"expected {expected_rule}, got {rule_ids}"


def test_good_fixture_has_zero_security_findings(good_root: Path):
    for sub in good_root.iterdir():
        if not sub.is_dir():
            continue
        inv = parse_path(sub)
        findings = run_scan(inv)
        assert findings == [], f"unexpected findings in {sub.name}: {findings}"


def test_rule_subprocess_not_called(monkeypatch, bad_root: Path):
    """The scanner must never call subprocess.run."""
    import subprocess as _sp

    called = {"run": False}

    def fake_run(*args, **kwargs):  # pragma: no cover - asserted below
        called["run"] = True
        raise AssertionError("subprocess.run was called")

    monkeypatch.setattr(_sp, "run", fake_run)
    inv = parse_path(bad_root)
    run_scan(inv)
    assert called["run"] is False


def test_engine_from_dirs_loads_yaml(tmp_path: Path):
    """Custom rule directory works and rejects bad input."""
    rule_dir = tmp_path / "rules"
    rule_dir.mkdir()
    (rule_dir / "custom.yaml").write_text(
        "rules:\n"
        "  - id: SEC-CUSTOM\n"
        "    name: custom\n"
        "    severity: low\n"
        "    engine: regex\n"
        "    targets: [body]\n"
        "    pattern: 'hello'\n"
        "    message: hello detected\n"
        "    remediation: say hi\n",
        encoding="utf-8",
    )
    engine = ScannerEngine.from_dirs([rule_dir])
    assert any(r.id == "SEC-CUSTOM" for r in engine.rules)


def test_engine_from_dirs_rejects_missing_dir(tmp_path: Path):
    from skillops_forge.exceptions import RuleLoadError

    with pytest.raises(RuleLoadError):
        ScannerEngine.from_dirs([tmp_path / "nope"])


def test_engine_rule_yaml_with_bad_root(tmp_path: Path):
    from skillops_forge.exceptions import RuleLoadError

    rule_dir = tmp_path / "rules"
    rule_dir.mkdir()
    (rule_dir / "bad.yaml").write_text("- not a mapping\n", encoding="utf-8")
    with pytest.raises(RuleLoadError):
        ScannerEngine.from_dirs([rule_dir])


def test_engine_rule_yaml_invalid(tmp_path: Path):
    from skillops_forge.exceptions import RuleLoadError

    rule_dir = tmp_path / "rules"
    rule_dir.mkdir()
    (rule_dir / "x.yaml").write_text("rules: not_a_list\n", encoding="utf-8")
    with pytest.raises(RuleLoadError):
        ScannerEngine.from_dirs([rule_dir])


def test_engine_rule_entry_must_be_mapping(tmp_path: Path):
    from skillops_forge.exceptions import RuleLoadError

    rule_dir = tmp_path / "rules"
    rule_dir.mkdir()
    (rule_dir / "x.yaml").write_text("rules:\n  - 'not a mapping'\n", encoding="utf-8")
    with pytest.raises(RuleLoadError):
        ScannerEngine.from_dirs([rule_dir])


def test_engine_bad_yaml_syntax(tmp_path: Path):
    from skillops_forge.exceptions import RuleLoadError

    rule_dir = tmp_path / "rules"
    rule_dir.mkdir()
    (rule_dir / "x.yaml").write_text("rules: [unbalanced\n", encoding="utf-8")
    with pytest.raises(RuleLoadError):
        ScannerEngine.from_dirs([rule_dir])
