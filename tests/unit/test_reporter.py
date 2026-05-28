from __future__ import annotations

import json
from pathlib import Path

from skillops_forge.pipeline import run_pipeline
from skillops_forge.reporter import render
from skillops_forge.reporter.html import render_html
from skillops_forge.reporter.markdown import render_markdown


def test_render_markdown_contains_required_sections(good_root: Path, tmp_path: Path):
    report = run_pipeline(good_root / "skill-md-basic")
    md = render_markdown(report)
    assert "# SkillOps Forge Report" in md
    assert "## Summary" in md
    assert "## Findings" in md
    assert "## Compliance Checklist" in md


def test_render_html_is_self_contained(good_root: Path):
    report = run_pipeline(good_root / "skill-md-basic")
    html = render_html(report)
    assert html.startswith("<!doctype html>")
    assert "<style>" in html
    # No external script/style references — offline by construction.
    assert "<link" not in html
    assert "https://cdn" not in html
    assert "SkillOps Forge" in html


def test_render_all_writes_three_files(good_root: Path, tmp_path: Path):
    report = run_pipeline(good_root / "skill-md-basic")
    written = render(report, fmt="all", out_dir=tmp_path)
    names = {p.name for p in written}
    assert names == {"skillops-report.md", "skillops-report.html", "skillops-result.json"}
    payload = json.loads((tmp_path / "skillops-result.json").read_text(encoding="utf-8"))
    assert payload["score"] == report.score
