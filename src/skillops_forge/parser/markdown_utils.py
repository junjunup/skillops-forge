"""Markdown helpers shared across parsers (frontmatter splitting, fenced blocks)."""

from __future__ import annotations

import re
from typing import Any

import yaml

from skillops_forge.models import Example

_FRONTMATTER_RE = re.compile(
    r"\A---\s*\r?\n(?P<fm>.*?)\r?\n---\s*\r?\n?(?P<body>.*)\Z",
    re.DOTALL,
)
_SECTION_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)
_FENCE_RE = re.compile(
    r"```(?P<lang>[a-zA-Z0-9_+-]*)\s*\r?\n(?P<body>.*?)```",
    re.DOTALL,
)


def split_frontmatter(text: str) -> tuple[dict[str, Any], str, list[str]]:
    """Split a document into ``(frontmatter_dict, body, parse_errors)``.

    Behaviour:
    * If no ``---`` block is present at the start, returns ``({}, text, [])``.
    * If the YAML block is malformed, returns ``({}, body, ["..."])`` —
      the parser must NEVER raise: a single broken file should not abort the
      whole pipeline. The body is still extracted so downstream auditors can
      keep working.
    * If the YAML parses but is not a mapping, returns ``({}, body, ["..."])``.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text, []
    raw_fm = match.group("fm")
    body = match.group("body")
    try:
        loaded = yaml.safe_load(raw_fm)
    except yaml.YAMLError as exc:
        # Compress the (often verbose, multi-line) YAML error into one line.
        first_line = str(exc).splitlines()[0] if str(exc) else "malformed YAML"
        return {}, body, [f"bad YAML frontmatter: {first_line[:200]}"]
    if loaded is None:
        return {}, body, []
    if not isinstance(loaded, dict):
        return (
            {},
            body,
            [f"frontmatter is not a YAML mapping (got {type(loaded).__name__})"],
        )
    return loaded, body, []


def extract_sections(body: str) -> dict[str, str]:
    """Slice the body into ``{section_title: section_text}`` by ``## headings``."""
    matches = list(_SECTION_RE.finditer(body))
    sections: dict[str, str] = {}
    if not matches:
        return sections
    for idx, m in enumerate(matches):
        title = m.group("title").strip()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        sections[title] = body[start:end].strip("\n")
    return sections


def extract_fenced_examples(body: str) -> list[Example]:
    """Best-effort extraction of fenced code blocks as :class:`Example` objects."""
    examples: list[Example] = []
    for idx, m in enumerate(_FENCE_RE.finditer(body), start=1):
        lang = m.group("lang").strip().lower()
        content = m.group("body").rstrip("\n")
        commands: tuple[str, ...] = ()
        if lang in {"bash", "sh", "shell", "zsh"}:
            commands = tuple(
                line.strip()
                for line in content.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            )
        examples.append(
            Example(
                title=f"Example {idx}",
                input=content,
                expected_output="",
                commands=commands,
                language=lang or "text",
            )
        )
    return examples


def extract_allowed_tools(frontmatter: dict[str, Any]) -> tuple[str, ...]:
    """Extract ``allowed-tools`` (or ``allowedTools``) entries as a tuple of strings."""
    raw = (
        frontmatter.get("allowed-tools")
        or frontmatter.get("allowedTools")
        or frontmatter.get("allowed_tools")
        or ()
    )
    if isinstance(raw, str):
        # comma-separated form: "Bash, Read, Write"
        return tuple(s.strip() for s in raw.split(",") if s.strip())
    if isinstance(raw, (list, tuple)):
        return tuple(str(s).strip() for s in raw if str(s).strip())
    return ()
