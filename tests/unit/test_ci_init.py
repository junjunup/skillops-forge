from __future__ import annotations

from pathlib import Path

from skillops_forge.ci import init_ci
from skillops_forge.ci.github_actions import render_workflow


def test_workflow_pinned_actions():
    yml = render_workflow()
    assert "actions/checkout@v4" in yml
    assert "actions/setup-python@v5" in yml
    assert "skillops scan" in yml
    assert "if-no-files-found" in yml


def test_init_ci_writes_file(tmp_path: Path):
    target = tmp_path / "wf.yml"
    written = init_ci(out=target)
    assert written == target
    assert target.exists()
    assert "SkillOps Forge" in target.read_text(encoding="utf-8")


def test_init_ci_refuses_overwrite(tmp_path: Path):
    target = tmp_path / "wf.yml"
    target.write_text("existing", encoding="utf-8")
    try:
        init_ci(out=target)
    except FileExistsError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected FileExistsError")


def test_init_ci_force_overwrites(tmp_path: Path):
    target = tmp_path / "wf.yml"
    target.write_text("existing", encoding="utf-8")
    init_ci(out=target, force=True)
    assert "actions/checkout@v4" in target.read_text(encoding="utf-8")
