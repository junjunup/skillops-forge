"""Parser package — detects skill format and dispatches to the right parser."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from skillops_forge import __version__
from skillops_forge.exceptions import ParseError
from skillops_forge.logging_setup import get_logger
from skillops_forge.models import SkillFile, SkillFormat, SkillInventory
from skillops_forge.parser.base import BaseParser
from skillops_forge.parser.claude_md import ClaudeMdParser
from skillops_forge.parser.cursor_rules import CursorRulesParser
from skillops_forge.parser.inventory import iter_skill_paths
from skillops_forge.parser.skill_md import SkillMdParser

FormatLiteral = Literal["skill_md", "claude_md", "cursor_rules", "unknown"]

_logger = get_logger()


def _all_parsers() -> tuple[BaseParser, ...]:
    return (SkillMdParser(), ClaudeMdParser(), CursorRulesParser())


def detect_format(path: Path) -> FormatLiteral:
    """Best-effort detection of a skill source format from a single file path."""
    name = path.name.lower()
    if name == "skill.md":
        return "skill_md"
    if name == "claude.md":
        return "claude_md"
    parts = {p.lower() for p in path.parts}
    if ".cursor" in parts and path.suffix.lower() in {".md", ".mdc"}:
        return "cursor_rules"
    return "unknown"


def parse_file(path: Path) -> SkillFile:
    """Parse a single file using the first parser that handles it."""
    for parser in _all_parsers():
        if parser.can_handle(path):
            return parser.parse(path)
    raise ParseError(f"no parser can handle: {path}")


def parse_path(
    target: Path,
    *,
    include_cursor_rules: bool = True,
) -> SkillInventory:
    """Walk ``target`` and produce a :class:`SkillInventory` of all skill files.

    Args:
        target: A file or a directory.
        include_cursor_rules: When False, ``.cursor/rules`` directories are skipped.

    Returns:
        A populated :class:`SkillInventory`. Individual files that fail to read
        (``OSError``) are logged and skipped — they should not abort the whole
        walk. YAML-level frontmatter problems are now captured inside each
        :class:`SkillFile` via ``parse_errors`` and surfaced as audit findings.
    """
    target = Path(target)
    files: list[SkillFile] = []
    for candidate in iter_skill_paths(target, include_cursor_rules=include_cursor_rules):
        for parser in _all_parsers():
            if parser.can_handle(candidate):
                try:
                    files.append(parser.parse(candidate))
                except ParseError as exc:
                    _logger.warning("skipping unreadable file %s: %s", candidate, exc)
                break
    root = target if target.is_dir() else target.parent
    return SkillInventory(
        root=root,
        files=tuple(files),
        tool_version=__version__,
    )


__all__ = [
    "FormatLiteral",
    "SkillFormat",
    "detect_format",
    "parse_file",
    "parse_path",
]
