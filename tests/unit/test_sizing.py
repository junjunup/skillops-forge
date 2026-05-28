"""Tests for v0.1.4 sizing audit (AUD-100/101/102) and the heuristic estimator."""

from __future__ import annotations

from pathlib import Path

import pytest

from skillops_forge.auditor.sizing import (
    LINE_WARNING_THRESHOLD,
    TOKEN_ERROR_THRESHOLD,
    TOKEN_WARNING_THRESHOLD,
    audit_sizing,
    estimate_tokens,
)
from skillops_forge.parser import parse_path

# ---------------------------------------------------------------------------
# estimate_tokens — heuristic / tiktoken parity sanity
# ---------------------------------------------------------------------------


def test_estimate_tokens_short_text_is_at_least_one() -> None:
    assert estimate_tokens("hello") >= 1


def test_estimate_tokens_grows_with_length() -> None:
    short = estimate_tokens("hello world")
    long = estimate_tokens("hello world " * 200)
    assert long > short
    # Heuristic should not be wildly off — 400 words ≈ a few hundred tokens.
    assert 200 < long < 3000


def test_estimate_tokens_handles_only_punctuation() -> None:
    # Pure punctuation should still be counted.
    n = estimate_tokens("!!!---***" * 20)
    assert n >= 1


# ---------------------------------------------------------------------------
# audit_sizing — line / token thresholds
# ---------------------------------------------------------------------------


def _write_skill(tmp_path: Path, body: str, name: str = "size-test") -> Path:
    path = tmp_path / "SKILL.md"
    path.write_text(
        f"""---
name: {name}
version: 0.1.0
author: tester
description: Use when verifying size budget enforcement of body content for SkillOps Forge.
---

# {name}

{body}

## Inputs

- text

## Outputs

- text
""",
        encoding="utf-8",
    )
    return path


def test_small_skill_is_below_all_size_thresholds(tmp_path: Path) -> None:
    inv = parse_path(_write_skill(tmp_path, "small body."))
    out = audit_sizing(inv.files[0])
    rule_ids = {f.id for f in out}
    assert "AUD-100" not in rule_ids
    assert "AUD-101" not in rule_ids
    assert "AUD-102" not in rule_ids


def test_long_body_triggers_aud100_line_count(tmp_path: Path) -> None:
    body = "\n".join(["filler line"] * (LINE_WARNING_THRESHOLD + 5))
    inv = parse_path(_write_skill(tmp_path, body))
    out = audit_sizing(inv.files[0])
    rule_ids = {f.id for f in out}
    assert "AUD-100" in rule_ids


def test_token_warn_emits_aud101(tmp_path: Path) -> None:
    body = "lorem ipsum " * 1800  # ~3500-5000 tokens depending on backend
    inv = parse_path(_write_skill(tmp_path, body))
    findings = audit_sizing(inv.files[0])
    ids = {f.id for f in findings}
    # We are firmly above the warn line but well under the error line.
    assert "AUD-101" in ids or "AUD-102" in ids
    assert estimate_tokens(body) >= TOKEN_WARNING_THRESHOLD


def test_token_error_emits_aud102(tmp_path: Path) -> None:
    body = "lorem ipsum dolor sit amet consectetur adipiscing elit " * 1500
    inv = parse_path(_write_skill(tmp_path, body))
    findings = audit_sizing(inv.files[0])
    ids = {f.id for f in findings}
    assert "AUD-102" in ids
    assert estimate_tokens(body) >= TOKEN_ERROR_THRESHOLD


@pytest.mark.parametrize(
    ("threshold", "expected"),
    [
        (TOKEN_WARNING_THRESHOLD, 4400),
        (TOKEN_ERROR_THRESHOLD, 8800),
        (LINE_WARNING_THRESHOLD, 500),
    ],
)
def test_thresholds_are_anthropic_aligned(threshold: int, expected: int) -> None:
    assert threshold == expected
