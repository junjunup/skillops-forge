from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from skillops_forge.cli import app

runner = CliRunner()


@pytest.mark.integration
def test_cli_help_lists_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "scan" in result.stdout
    assert "init-ci" in result.stdout
    assert "version" in result.stdout


@pytest.mark.integration
def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "skillops-forge" in result.stdout


@pytest.mark.integration
def test_cli_scan_good_returns_zero(tmp_path: Path, good_root: Path):
    result = runner.invoke(
        app,
        [
            "scan",
            str(good_root / "skill-md-basic"),
            "--report",
            "all",
            "--out-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert (tmp_path / "skillops-report.md").exists()
    assert (tmp_path / "skillops-report.html").exists()
    payload = json.loads((tmp_path / "skillops-result.json").read_text(encoding="utf-8"))
    assert payload["is_passed"] is True


@pytest.mark.integration
def test_cli_scan_bad_returns_one(tmp_path: Path, bad_root: Path):
    result = runner.invoke(
        app,
        [
            "scan",
            str(bad_root / "curl-pipe-bash"),
            "--report",
            "json",
            "--out-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 1
    payload = json.loads((tmp_path / "skillops-result.json").read_text(encoding="utf-8"))
    assert payload["is_passed"] is False


@pytest.mark.integration
def test_cli_scan_missing_path_returns_two():
    result = runner.invoke(app, ["scan", "/this/does/not/exist"])
    assert result.exit_code == 2


@pytest.mark.integration
def test_cli_init_ci_writes_workflow(tmp_path: Path):
    out = tmp_path / "wf.yml"
    result = runner.invoke(app, ["init-ci", "--out", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert "actions/checkout@v4" in out.read_text(encoding="utf-8")
