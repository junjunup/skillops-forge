"""Permission-summary extractor (RPT-A).

Aggregates ``files_read`` / ``files_write`` / ``commands`` / ``network``
references across all skill files in an inventory, so the report header can
display "permissions this skill asks for at a glance" — mirroring the
``PERMISSIONS NEEDED`` section of skill-vetter's three-step audit.
"""

from __future__ import annotations

import re
import shlex

from skillops_forge.models import (
    PermissionSummary,
    SkillFile,
    SkillInventory,
)

# ---------------------------------------------------------------------------
# Regular expressions used by the heuristics
# ---------------------------------------------------------------------------

# A *path-ish* token: starts with ~, /, ./, ../, $VAR, drive-letter, or
# contains a slash/backslash. We deliberately exclude bare URLs (those go to
# the ``network`` bucket).
_PATH_TOKEN_RE = re.compile(
    r"""
    (?<![A-Za-z0-9_])                # left boundary: not part of an identifier
    (?:
        (?:~|\$\w+|\.{1,2}/|/|[A-Za-z]:[\\/])  # path prefix
        [\w./\\\-]+
    )
    """,
    re.VERBOSE,
)

# A read-action token immediately followed by one or more arguments.
_READ_RE = re.compile(
    r"\b(?:cat|less|more|head|tail|read_text|read_bytes|json\.loads|yaml\.safe_load|open)\b",
    re.IGNORECASE,
)
# Common write-action tokens. We also detect shell redirection separately.
_WRITE_RE = re.compile(
    r"\b(?:write_text|write_bytes|json\.dump(?:s)?|tee|cp|mv|install)\b",
    re.IGNORECASE,
)
_REDIRECT_RE = re.compile(r"(?:>{1,2}|\|\s*tee\b)\s*([\w./\\\-~$]+)")

_NETWORK_RE = re.compile(
    r"(?:\b(?:curl|wget|fetch|http\.get|requests\.(?:get|post|put|delete)|httpx\.\w+)\b[^\n]*?"
    r"(https?://[^\s'\"`)]+)|(https?://[^\s'\"`)]+))",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_permission_summary(inventory: SkillInventory) -> PermissionSummary:
    """Aggregate read/write/commands/network across every file in ``inventory``.

    The function is intentionally tolerant: parser failures (broken YAML, etc.)
    are quietly ignored — the returned summary will simply contain whatever
    could be extracted from healthy parts of each file.
    """
    files_read: set[str] = set()
    files_write: set[str] = set()
    commands: set[str] = set()
    network: set[str] = set()

    for skill in inventory.files:
        _harvest_skill(skill, files_read, files_write, commands, network)

    return PermissionSummary(
        files_read=_sorted(files_read),
        files_write=_sorted(files_write),
        commands=_sorted(commands),
        network=_sorted(network),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _harvest_skill(
    skill: SkillFile,
    files_read: set[str],
    files_write: set[str],
    commands: set[str],
    network: set[str],
) -> None:
    # Collect every searchable text fragment from a skill.
    fragments: list[str] = []
    if skill.body:
        fragments.append(skill.body)
    for example in skill.examples:
        if example.input:
            fragments.append(example.input)
        for cmd in example.commands:
            if cmd:
                fragments.append(cmd)
                _record_command(cmd, commands)

    for fragment in fragments:
        # network URLs first (cheap)
        for match in _NETWORK_RE.finditer(fragment):
            url = match.group(1) or match.group(2)
            if url:
                network.add(url.rstrip(".,);"))
        # read/write actions: scan line-by-line so the matched action and the
        # nearest path-ish token live on the same line.
        for line in fragment.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            _record_paths_for_line(stripped, files_read, files_write)


def _record_command(cmd: str, commands: set[str]) -> None:
    """Pull the leading executable name from a single shell command line."""
    line = cmd.strip()
    if not line:
        return
    try:
        tokens = shlex.split(line, posix=True)
    except ValueError:
        # Tokenization failed (e.g. unterminated quote); fall back to first word.
        tokens = line.split()
    if not tokens:
        return
    head = tokens[0]
    # Strip quotes / leading $ / backslashes.
    head = head.strip("'\"`")
    if head and not head.startswith("#"):
        commands.add(head)


def _record_paths_for_line(
    line: str,
    files_read: set[str],
    files_write: set[str],
) -> None:
    paths_in_line = [m.group(0) for m in _PATH_TOKEN_RE.finditer(line)]
    if not paths_in_line:
        return
    is_read = bool(_READ_RE.search(line))
    is_write = bool(_WRITE_RE.search(line))
    redirect_targets = [m.group(1) for m in _REDIRECT_RE.finditer(line)]

    if redirect_targets:
        for target in redirect_targets:
            files_write.add(target)
    if is_write and not redirect_targets:
        # take the *last* path on the line as the write target (tee/cp/mv)
        files_write.add(paths_in_line[-1])
    if is_read:
        for path in paths_in_line:
            # Don't double-count the same path as both read and write.
            if path not in files_write:
                files_read.add(path)


def _sorted(values: set[str]) -> tuple[str, ...]:
    """Return a deterministic, deduplicated tuple."""
    return tuple(sorted(v for v in values if v))


__all__ = ["extract_permission_summary"]
