from __future__ import annotations

from pathlib import Path

import pytest

from skillops_forge.models import Severity
from skillops_forge.pipeline import run_pipeline


@pytest.mark.integration
@pytest.mark.parametrize(
    "fixture",
    [
        "skill-md-basic",
        "skill-md-with-examples",
        "skill-md-permissioned",
        "claude-md-basic",
        "cursor-rules-basic",
    ],
)
def test_pipeline_passes_for_good_fixture(good_root: Path, fixture: str):
    report = run_pipeline(good_root / fixture)
    assert report.is_passed, report.summary()
    assert report.security_findings == ()
    assert report.audit_findings == ()


@pytest.mark.integration
@pytest.mark.parametrize(
    "fixture",
    [
        "missing-frontmatter",
        "curl-pipe-bash",
        "sensitive-path-aws",
        "hidden-zerowidth",
        "rm-rf-root",
        "base64-blob",
    ],
)
def test_pipeline_fails_for_bad_fixture(bad_root: Path, fixture: str):
    report = run_pipeline(bad_root / fixture)
    assert not report.is_passed, report.summary()


@pytest.mark.integration
def test_critical_veto_overrides_score(bad_root: Path):
    report = run_pipeline(bad_root / "curl-pipe-bash")
    has_critical = any(f.severity == Severity.CRITICAL for f in report.security_findings)
    assert has_critical
    assert report.is_passed is False


@pytest.mark.integration
def test_pipeline_continues_on_bad_frontmatter(tmp_path: Path):
    """A single file with malformed YAML must not abort the whole pipeline.

    The good file should still be parsed/audited normally; the bad one should
    yield exactly one CRITICAL audit finding (category=frontmatter) and no
    cascading high-severity errors about missing required fields. Overall
    pipeline ``is_passed`` must be False because of the CRITICAL veto.
    """
    good_dir = tmp_path / "good-skill"
    good_dir.mkdir()
    (good_dir / "SKILL.md").write_text(
        "---\n"
        "name: good-skill\n"
        "description: >-\n"
        "  Use this skill when you need to demonstrate a well-formed example\n"
        "  with a proper folded scalar.\n"
        "---\n"
        "\n"
        "## Inputs\nx\n\n## Outputs\ny\n",
        encoding="utf-8",
    )
    bad_dir = tmp_path / "bad-skill"
    bad_dir.mkdir()
    # Multi-line description with a stray colon on the continuation line —
    # exactly the humanizer SKILL.md failure mode reported in the field
    # ("while scanning a simple key").
    (bad_dir / "SKILL.md").write_text(
        "---\n"
        "name: bad-skill\n"
        "description: Use this when you want to break the\n"
        "    yaml parser because the second line: has an unquoted colon\n"
        "    that PyYAML refuses to accept.\n"
        "---\n"
        "\n"
        "## Inputs\n\n```bash\necho hi\n```\n",
        encoding="utf-8",
    )

    report = run_pipeline(tmp_path)

    assert len(report.inventory.files) == 2
    bad_findings = [
        f for f in report.audit_findings if "bad-skill" in str(f.file).replace("\\", "/")
    ]
    critical_bad = [f for f in bad_findings if f.severity == Severity.CRITICAL]
    assert len(critical_bad) == 1, bad_findings
    assert critical_bad[0].category == "frontmatter"
    # No cascade: AUD-001/AUD-002 should NOT fire on the broken file.
    assert not any(f.id in {"AUD-001", "AUD-002"} for f in bad_findings)
    assert report.is_passed is False
    assert report.overall_risk == Severity.CRITICAL
