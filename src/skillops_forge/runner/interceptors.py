"""Command interceptors for the runner.

Each ``inspect_command`` invocation returns a verdict structure describing what
would have happened and whether the runner blocked the action. **Nothing is
actually executed.**
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path

from skillops_forge.models import Severity

# Commands always considered safe to *symbolically* run.
_ALLOW_PREFIXES: frozenset[str] = frozenset(
    {
        "echo",
        "printf",
        "cat",
        "ls",
        "pwd",
        "head",
        "tail",
        "grep",
        "find",
        "cd",
        "true",
        "false",
        "python",
        "python3",
        "pip",
        "git",
        "skillops",
    }
)

# Commands always rejected.
_DENY_PREFIXES: frozenset[str] = frozenset(
    {
        "rm",
        "dd",
        "mkfs",
        "shutdown",
        "reboot",
        "halt",
        "kill",
        "killall",
        "chown",
        "chmod",
        "sudo",
        "su",
        "ssh",
        "scp",
        "rsync",
        "nc",
        "ncat",
        "tcpdump",
    }
)

_PIPE_TO_SHELL_RE = re.compile(r"\b(?:curl|wget)\s+[^|;&\n]*?\|\s*(?:sh|bash|zsh|ksh)\b")


@dataclass(frozen=True)
class Verdict:
    """Static verdict for a single command line."""

    kind: str  # "allow" | "warn" | "block"
    reason: str
    severity: Severity | None
    remediation: str = ""


def inspect_command(command: str, *, skill_path: Path | None = None) -> Verdict:
    """Statically classify a single command line.

    Args:
        command: A single command string (one line).
        skill_path: Optional originating skill path (currently informational only).

    Returns:
        A :class:`Verdict`.
    """
    _ = skill_path  # reserved for future heuristics
    text = command.strip()
    if not text:
        return Verdict("allow", "empty command", severity=None)
    if _PIPE_TO_SHELL_RE.search(text):
        return Verdict(
            "block",
            "pipe-to-shell pattern (curl|wget piped into sh/bash)",
            severity=Severity.CRITICAL,
            remediation="Download, verify checksum, then execute.",
        )
    try:
        tokens = shlex.split(text, posix=True)
    except ValueError:
        # Unparseable shell — treat as warn so we don't false-positive.
        return Verdict("warn", "could not tokenize command", severity=Severity.LOW)
    if not tokens:
        return Verdict("allow", "no tokens", severity=None)
    head = tokens[0].lower()
    if head in _DENY_PREFIXES:
        return Verdict(
            "block",
            f"denied command prefix '{head}'",
            severity=Severity.HIGH,
            remediation="Never demonstrate destructive/privileged commands directly.",
        )
    if head in _ALLOW_PREFIXES:
        return Verdict("allow", f"allowed prefix '{head}'", severity=None)
    return Verdict("warn", f"unknown command prefix '{head}'", severity=Severity.LOW)


__all__ = ["Verdict", "inspect_command"]
