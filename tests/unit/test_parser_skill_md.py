from __future__ import annotations

from pathlib import Path

from skillops_forge.models import SkillFormat
from skillops_forge.parser import detect_format, parse_file, parse_path
from skillops_forge.parser.markdown_utils import split_frontmatter
from skillops_forge.parser.skill_md import SkillMdParser


def test_skill_md_parser_extracts_frontmatter_and_examples(good_root: Path):
    skill = parse_file(good_root / "skill-md-basic" / "SKILL.md")
    assert skill.format == SkillFormat.SKILL_MD
    assert skill.frontmatter["name"] == "skill-md-basic"
    assert "description" in skill.frontmatter
    assert skill.allowed_tools == ("Read",)
    assert len(skill.examples) >= 1
    assert "Inputs" in skill.sections


def test_inventory_walks_directory(good_root: Path):
    inv = parse_path(good_root)
    formats = {f.format for f in inv.files}
    assert SkillFormat.SKILL_MD in formats
    assert SkillFormat.CLAUDE_MD in formats
    assert SkillFormat.CURSOR_RULES in formats


def test_detect_format(good_root: Path):
    assert detect_format(good_root / "skill-md-basic" / "SKILL.md") == "skill_md"
    assert detect_format(good_root / "claude-md-basic" / "CLAUDE.md") == "claude_md"
    cursor = good_root / "cursor-rules-basic" / ".cursor" / "rules" / "python-style.mdc"
    assert detect_format(cursor) == "cursor_rules"
    assert detect_format(good_root / "skill-md-basic" / "SKILL.md").startswith("skill")


def test_parse_path_skips_cursor_when_disabled(good_root: Path):
    inv = parse_path(good_root, include_cursor_rules=False)
    formats = {f.format for f in inv.files}
    assert SkillFormat.CURSOR_RULES not in formats


def test_split_frontmatter_handles_malformed_yaml():
    """Bad YAML must NOT raise — return empty fm + capture error message."""
    text = "---\nname: foo\ndescription: line-one\n    line-two-but-bad-indent: oops\n---\n\nbody\n"
    fm, body, errors = split_frontmatter(text)
    assert fm == {}
    assert body.strip() == "body"
    assert len(errors) == 1
    assert "bad YAML frontmatter" in errors[0]


def test_split_frontmatter_handles_non_mapping_yaml():
    """A YAML scalar/list at the root must be reported, not raised."""
    text = "---\n- just-a-list\n---\nbody\n"
    fm, body, errors = split_frontmatter(text)
    assert fm == {}
    assert body.strip() == "body"
    assert errors and "not a YAML mapping" in errors[0]


def test_split_frontmatter_handles_empty_yaml():
    """An effectively empty YAML block is legal — no errors, empty mapping."""
    text = "---\n\n---\nbody\n"
    fm, body, errors = split_frontmatter(text)
    assert fm == {}
    assert body.strip() == "body"
    assert errors == []


def test_malformed_frontmatter_degrades_gracefully(tmp_path: Path):
    """Reproduces the humanizer SKILL.md failure mode — must not raise.

    The humanizer file in the field has a top-level ``description:`` mapping
    key whose value continues on later lines that look like more mapping keys
    (``yaml: ...`` indented or at col 0). PyYAML rejects this with
    ``mapping values are not allowed here`` / ``while scanning a simple key``
    — exactly the error reported against the real installed skills tree.
    """
    bad = tmp_path / "SKILL.md"
    bad.write_text(
        "---\n"
        "name: humanizer-like\n"
        "description: Remove signs of AI-generated writing from text. Use when\n"
        "    editing or reviewing text to make it sound more natural and\n"
        "    human-written: indented colon makes this a parse error\n"
        "---\n"
        "\n"
        "## Inputs\n\nstuff\n",
        encoding="utf-8",
    )
    skill = SkillMdParser().parse(bad)
    assert skill.frontmatter == {}
    assert skill.parse_errors  # non-empty
    assert skill.parse_errors[0].startswith("bad YAML frontmatter")
    # Body / sections must still be extracted regardless of the YAML failure.
    assert "Inputs" in skill.sections
