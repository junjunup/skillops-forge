from __future__ import annotations

from pathlib import Path

from skillops_forge.models import SkillFormat
from skillops_forge.parser import parse_file


def test_claude_md_parser(good_root: Path):
    skill = parse_file(good_root / "claude-md-basic" / "CLAUDE.md")
    assert skill.format == SkillFormat.CLAUDE_MD
    # claude_md does not require frontmatter; it should still parse.
    assert "Overview" in skill.sections
    assert "Examples" in skill.sections
    assert any(e.language in {"bash", "sh"} for e in skill.examples)
