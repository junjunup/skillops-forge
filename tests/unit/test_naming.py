"""Tests for v0.1.4 naming/description/unknown-field rules (AUD-110..130)."""

from __future__ import annotations

from pathlib import Path

import pytest

from skillops_forge.auditor.naming import audit_naming
from skillops_forge.parser import parse_path


def _write(
    tmp_path: Path,
    frontmatter: str,
    body: str = "Use when testing.\n\n## Inputs\n- a\n\n## Outputs\n- b\n",
) -> Path:
    p = tmp_path / "SKILL.md"
    p.write_text(f"---\n{frontmatter}\n---\n\n# T\n\n{body}", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Name rules — AUD-110/111/112
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_name",
    [
        "MySkill",  # uppercase
        "my_skill",  # underscore
        "-leading-hyphen",
        "trailing-hyphen-",
        "double--hyphen",
        "name@with$symbol",
    ],
)
def test_aud110_kebab_case_violations(tmp_path: Path, bad_name: str) -> None:
    inv = parse_path(
        _write(
            tmp_path,
            f"name: {bad_name}\nversion: 0.1.0\nauthor: t\ndescription: Use when testing the kebab-case rule.",
        )
    )
    out = audit_naming(inv.files[0])
    assert any(f.id == "AUD-110" for f in out), [f.id for f in out]


def test_aud111_name_too_long(tmp_path: Path) -> None:
    long_name = "a-" * 33  # 66 chars > 64
    inv = parse_path(
        _write(
            tmp_path,
            f"name: {long_name}\nversion: 0.1.0\nauthor: t\ndescription: Use when verifying name length cap.",
        )
    )
    out = audit_naming(inv.files[0])
    assert any(f.id == "AUD-111" for f in out)


@pytest.mark.parametrize(
    "token", ["claude-helper", "my-anthropic-tool", "openai-skill", "cursor-bridge"]
)
def test_aud112_reserved_vendor_tokens(tmp_path: Path, token: str) -> None:
    inv = parse_path(
        _write(
            tmp_path,
            f"name: {token}\nversion: 0.1.0\nauthor: t\ndescription: Use when verifying reserved vendor token detection.",
        )
    )
    out = audit_naming(inv.files[0])
    assert any(f.id == "AUD-112" for f in out), [f.id for f in out]


def test_valid_name_clean(tmp_path: Path) -> None:
    inv = parse_path(
        _write(
            tmp_path,
            "name: my-skill\nversion: 0.1.0\nauthor: t\ndescription: Use when verifying that valid names produce no naming finding.",
        )
    )
    out = audit_naming(inv.files[0])
    name_ids = {f.id for f in out if f.id in {"AUD-110", "AUD-111", "AUD-112"}}
    assert name_ids == set()


# ---------------------------------------------------------------------------
# Description rules — AUD-120..126
# ---------------------------------------------------------------------------


def test_aud120_description_too_long(tmp_path: Path) -> None:
    long = "Use when " + ("very long description text " * 60)
    inv = parse_path(_write(tmp_path, f"name: x\nversion: 0.1.0\nauthor: t\ndescription: {long}"))
    out = audit_naming(inv.files[0])
    assert any(f.id == "AUD-120" for f in out)


def test_aud121_description_too_short(tmp_path: Path) -> None:
    inv = parse_path(_write(tmp_path, "name: x\nversion: 0.1.0\nauthor: t\ndescription: Use it"))
    out = audit_naming(inv.files[0])
    assert any(f.id == "AUD-121" for f in out)


def test_aud122_description_xml_tags(tmp_path: Path) -> None:
    inv = parse_path(
        _write(
            tmp_path,
            'name: x\nversion: 0.1.0\nauthor: t\ndescription: "Use when <b>bold</b> markup is involved in the skill description."',
        )
    )
    out = audit_naming(inv.files[0])
    assert any(f.id == "AUD-122" for f in out)


def test_aud123_first_person_voice(tmp_path: Path) -> None:
    inv = parse_path(
        _write(
            tmp_path,
            'name: x\nversion: 0.1.0\nauthor: t\ndescription: "I will do things when this skill is loaded by the agent runtime."',
        )
    )
    out = audit_naming(inv.files[0])
    assert any(f.id == "AUD-123" for f in out)


def test_aud124_second_person_voice(tmp_path: Path) -> None:
    inv = parse_path(
        _write(
            tmp_path,
            'name: x\nversion: 0.1.0\nauthor: t\ndescription: "You should run this skill when checking second-person voice rule."',
        )
    )
    out = audit_naming(inv.files[0])
    assert any(f.id == "AUD-124" for f in out)


def test_aud125_multiline_description(tmp_path: Path) -> None:
    # Use ``|`` (literal block scalar) so PyYAML keeps the newline in the
    # parsed string, matching what the AUD-125 detector observes.
    fm = (
        "name: x\nversion: 0.1.0\nauthor: t\n"
        "description: |\n"
        "  Use when verifying that block scalar descriptions get flagged\n"
        "  by the multiline AUD-125 rule.\n"
    )
    inv = parse_path(_write(tmp_path, fm))
    out = audit_naming(inv.files[0])
    assert any(f.id == "AUD-125" for f in out)


def test_aud126_missing_trigger_phrase(tmp_path: Path) -> None:
    # No trigger phrase from the 11-entry list.
    inv = parse_path(
        _write(
            tmp_path,
            'name: x\nversion: 0.1.0\nauthor: t\ndescription: A static analyzer for skill packs that emits findings."',
        )
    )
    out = audit_naming(inv.files[0])
    # NOTE: "static analyzer" lacks any trigger phrase from the list.
    ids = {f.id for f in out}
    assert "AUD-126" in ids


def test_trigger_phrase_recognised(tmp_path: Path) -> None:
    inv = parse_path(
        _write(
            tmp_path,
            "name: x\nversion: 0.1.0\nauthor: t\ndescription: Use when validating the new trigger phrase recogniser logic in v0.1.4.",
        )
    )
    out = audit_naming(inv.files[0])
    ids = {f.id for f in out}
    assert "AUD-126" not in ids


# ---------------------------------------------------------------------------
# Unknown frontmatter field — AUD-130
# ---------------------------------------------------------------------------


def test_aud130_unknown_field_warning(tmp_path: Path) -> None:
    inv = parse_path(
        _write(
            tmp_path,
            "name: x\nversion: 0.1.0\nauthor: t\ndescription: Use when verifying unknown-field detection.\nzzz_unknown: weird",
        )
    )
    out = audit_naming(inv.files[0])
    assert any(f.id == "AUD-130" and f.field == "zzz_unknown" for f in out)


def test_known_fields_no_aud130(tmp_path: Path) -> None:
    inv = parse_path(
        _write(
            tmp_path,
            "name: x\nversion: 0.1.0\nauthor: t\nsource: https://example.com/skills\ntags: [test]\ndescription: Use when verifying that all known fields are tolerated.",
        )
    )
    out = audit_naming(inv.files[0])
    assert not any(f.id == "AUD-130" for f in out), [f.field for f in out if f.id == "AUD-130"]
