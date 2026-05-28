"""Heuristic detectors used by the scanner.

These are intentionally conservative — false positives erode trust faster than
they catch real issues.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from skillops_forge.config import (
    BASE64_LINE_LENGTH_THRESHOLD,
    ENTROPY_THRESHOLD,
    EXFIL_ALLOWED_DOMAINS,
    ZERO_WIDTH_CHARS,
)

_BASE64_LINE_RE = re.compile(
    rf"^[A-Za-z0-9+/=]{{{BASE64_LINE_LENGTH_THRESHOLD},}}$",
    re.MULTILINE,
)
_URL_RE = re.compile(r"https?://([\w.\-]+)(/[^\s'\"`<>]*)?", re.IGNORECASE)
_FETCH_HINTS = (
    "curl",
    "wget",
    "requests.",
    "fetch(",
    "http.get",
    "httpx.",
    "urllib",
)


def shannon_entropy(s: str) -> float:
    """Return the Shannon entropy (bits/symbol) for ``s``."""
    if not s:
        return 0.0
    counts = Counter(s)
    total = len(s)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def detect_zero_width(text: str) -> list[tuple[int, int, str]]:
    """Return (line, col, matched) for every zero-width character occurrence."""
    out: list[tuple[int, int, str]] = []
    for idx, ch in enumerate(text):
        if ch in ZERO_WIDTH_CHARS:
            line, col = _line_col(text, idx)
            out.append((line, col, repr(ch)))
    return out


def detect_high_entropy_base64(text: str) -> list[tuple[int, int, str]]:
    """Return long base64-like lines whose entropy exceeds the threshold."""
    out: list[tuple[int, int, str]] = []
    for m in _BASE64_LINE_RE.finditer(text):
        sample = m.group(0)
        if shannon_entropy(sample) >= ENTROPY_THRESHOLD:
            line, col = _line_col(text, m.start())
            out.append((line, col, sample[:80] + ("…" if len(sample) > 80 else "")))
    return out


def detect_unallowlisted_exfil(text: str) -> list[tuple[int, int, str]]:
    """Flag URLs to non-allowlisted hosts on lines containing fetch hints."""
    out: list[tuple[int, int, str]] = []
    lines = text.splitlines()
    cumulative = 0
    for lineno, raw_line in enumerate(lines, start=1):
        line_lower = raw_line.lower()
        if any(h in line_lower for h in _FETCH_HINTS):
            for m in _URL_RE.finditer(raw_line):
                host = m.group(1).lower()
                if not _is_allowed(host):
                    col = m.start() + 1
                    matched = raw_line[m.start() : m.end()]
                    _ = cumulative  # not used; keep loop simple
                    out.append((lineno, col, matched))
        cumulative += len(raw_line) + 1
    return out


def _is_allowed(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in EXFIL_ALLOWED_DOMAINS)


def _line_col(text: str, offset: int) -> tuple[int, int]:
    if offset <= 0:
        return 1, 1
    head = text[:offset]
    line = head.count("\n") + 1
    last_nl = head.rfind("\n")
    col = offset - last_nl if last_nl >= 0 else offset + 1
    return line, col


__all__ = [
    "detect_high_entropy_base64",
    "detect_unallowlisted_exfil",
    "detect_zero_width",
    "shannon_entropy",
]
