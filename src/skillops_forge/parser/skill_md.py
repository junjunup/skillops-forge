"""Parser for ``SKILL.md`` files (YAML frontmatter + Markdown body)."""

from __future__ import annotations

from pathlib import Path

from skillops_forge.exceptions import ParseError
from skillops_forge.models import SkillFile, SkillFormat
from skillops_forge.parser.base import BaseParser
from skillops_forge.parser.markdown_utils import (
    extract_allowed_tools,
    extract_fenced_examples,
    extract_sections,
    split_frontmatter,
)


class SkillMdParser(BaseParser):
    """Parses ``SKILL.md`` style files with YAML frontmatter."""

    suffixes = (".md",)

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".md" and path.name.lower() == "skill.md"

    def parse(self, path: Path) -> SkillFile:
        try:
            text = self.read_text(path)
        except OSError as exc:
            raise ParseError(f"cannot read {path}: {exc}") from exc
        frontmatter, body, parse_errors = split_frontmatter(text)
        sections = extract_sections(body)
        examples = extract_fenced_examples(body)
        allowed_tools = extract_allowed_tools(frontmatter)
        return SkillFile(
            path=path,
            format=SkillFormat.SKILL_MD,
            frontmatter=frontmatter,
            body=body,
            allowed_tools=allowed_tools,
            examples=tuple(examples),
            sha256=SkillFile.compute_sha256(text),
            line_count=text.count("\n") + 1,
            sections=sections,
            parse_errors=tuple(parse_errors),
        )
