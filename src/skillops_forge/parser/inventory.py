"""Filesystem walking helpers used by the parser package."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

# Directories to never descend into while searching for skills.
_SKIP_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "build",
        "dist",
        "reports",
        "site-packages",
    }
)


def iter_skill_paths(
    target: Path,
    *,
    include_cursor_rules: bool = True,
) -> Iterator[Path]:
    """Yield all skill source files under ``target``.

    Args:
        target: A file or a directory.
        include_cursor_rules: When False, skip the ``.cursor/rules`` tree.

    Yields:
        Paths to ``SKILL.md``, ``CLAUDE.md`` or ``.cursor/rules/*.md(c)``.
    """
    target = Path(target)
    if target.is_file():
        yield target
        return
    if not target.exists():
        return
    for path in _walk(target, include_cursor_rules=include_cursor_rules):
        if _matches(path):
            yield path


def _walk(root: Path, *, include_cursor_rules: bool) -> Iterator[Path]:
    """Depth-first walk that prunes ignored directories deterministically."""
    stack: list[Path] = [root]
    while stack:
        current = stack.pop()
        if current.is_dir():
            name_lower = current.name.lower()
            if name_lower in _SKIP_DIRS:
                continue
            if not include_cursor_rules and name_lower == ".cursor":
                continue
            try:
                children = sorted(current.iterdir(), key=lambda p: p.name)
            except OSError:
                continue
            # iterate in stable order: files first, then dirs
            files = [p for p in children if p.is_file()]
            dirs = [p for p in children if p.is_dir()]
            yield from files
            stack.extend(reversed(dirs))
        elif current.is_file():
            yield current


def _matches(path: Path) -> bool:
    name = path.name.lower()
    if name in {"skill.md", "claude.md"}:
        return True
    if path.suffix.lower() in {".md", ".mdc"}:
        parts = {p.lower() for p in path.parts}
        if ".cursor" in parts:
            return True
    return False
