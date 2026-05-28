from __future__ import annotations

from pathlib import Path

from skillops_forge.models import SkillFormat
from skillops_forge.parser import parse_file


def test_cursor_rules_parser(good_root: Path):
    path = good_root / "cursor-rules-basic" / ".cursor" / "rules" / "python-style.mdc"
    skill = parse_file(path)
    assert skill.format == SkillFormat.CURSOR_RULES
    assert "globs" in skill.frontmatter
    assert any(e.language == "python" for e in skill.examples)
