"""Tests for v0.1.3 scanner-level finding deduplication."""

from __future__ import annotations

from pathlib import Path

from skillops_forge.parser import parse_path
from skillops_forge.scanner import ScannerEngine, run_scan


def test_duplicate_findings_are_deduplicated(tmp_path: Path) -> None:
    """A single ``sudo`` mention in the body must yield exactly one SEC-006
    finding, even when multiple rule targets (body / examples / all) overlap.

    Note: keep the description free of the trigger keyword so the only
    legitimate match is the body line; without dedup the engine produces
    duplicate findings (same rule_id, file, line, matched_text)."""
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        """---
name: dup-test
version: 0.1.0
author: tester
description: Use this skill when testing scanner deduplication on overlapping targets.
---

# Dup test

This skill demonstrates a privileged operation: sudo rm /tmp/x in a single line.

## Inputs

- text

## Outputs

- text
""",
        encoding="utf-8",
    )

    inv = parse_path(skill)
    findings = run_scan(inv)
    sec006 = [f for f in findings if f.rule_id == "SEC-006"]
    assert len(sec006) == 1, f"expected 1 SEC-006 finding, got {len(sec006)}: {sec006}"


def test_same_rule_different_matched_text_kept(tmp_path: Path) -> None:
    """If a rule legitimately matches different text fragments at different
    locations, both should be kept (dedup keys differ)."""
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        """---
name: dup-test
version: 0.1.0
author: tester
description: Use this skill when verifying that distinct matched text is preserved.
---

# Dup test

Line A references Read SOUL.md to remember identity.
Line B also references Read USER.md for context.

## Inputs

- ctx

## Outputs

- ctx
""",
        encoding="utf-8",
    )

    inv = parse_path(skill)
    findings = run_scan(inv)
    sec012 = [f for f in findings if f.rule_id == "SEC-012"]
    # Two distinct matches: SOUL.md and USER.md
    matched = sorted({f.matched_text for f in sec012})
    assert len(matched) == 2, f"expected 2 distinct matches, got {matched}"


def test_engine_scan_dedups_at_engine_layer(tmp_path: Path) -> None:
    """ScannerEngine.scan itself (not the run_scan wrapper) must dedup."""
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text(
        """---
name: dedup
version: 0.1.0
author: t
description: Use this skill when verifying scanner-layer deduplication overlap.
---

# Body
chmod 777 file.txt

## Inputs
- p
## Outputs
- p
""",
        encoding="utf-8",
    )
    inv = parse_path(skill_path)
    engine = ScannerEngine.from_builtins()
    raw = engine.scan(inv.files[0])
    sec006 = [f for f in raw if f.rule_id == "SEC-006"]
    assert len(sec006) == 1
