"""Audit: body size budgets (line count + token estimate).

Inspired by skilllint TC001 / SK006-SK007 (Anthropic-aligned budget thresholds)
and skillcheck (offline heuristic estimator).

The estimator prefers ``tiktoken`` (cl100k_base, ~5%% error) when installed and
falls back to a word/punct-run heuristic with ~15%% error so SkillOps Forge can
report sizing budgets without any third-party dependency.
"""

from __future__ import annotations

import re

from skillops_forge.models import AuditFinding, Severity, SkillFile, SkillFormat

# Anthropic-aligned thresholds (source: skilllint/token_counter.py).
TOKEN_WARNING_THRESHOLD: int = 4400
TOKEN_ERROR_THRESHOLD: int = 8800

# Body line-count warning threshold (skillcheck default).
LINE_WARNING_THRESHOLD: int = 500

_WORD_RE = re.compile(r"\w+")
_PUNCT_RE = re.compile(r"[^\w\s]+")


def estimate_tokens(text: str) -> int:
    """Estimate BPE token count for *text*.

    Priority:
        1. ``tiktoken`` (``cl100k_base``) if installed — ~5%% error, fully offline.
        2. Word/punct heuristic — ~15%% error, no dependencies.

    Neither yields exact Anthropic counts (their vocabulary is not public),
    but both are accurate enough for warning-level budget checks.
    """
    try:
        import tiktoken  # type: ignore[import-not-found]

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        pass
    word_tokens = int(len(_WORD_RE.findall(text)) * 1.3)
    punct_tokens = int(len(_PUNCT_RE.findall(text)) * 1.5)
    return max(1, word_tokens + punct_tokens)


def audit_sizing(skill: SkillFile) -> list[AuditFinding]:
    """Emit AUD-100 (line count), AUD-101 (token warn), AUD-102 (token error).

    Only enforces on SKILL.md / CLAUDE.md / cursor rules — every supported
    format has a token budget that affects context-window cost.
    """
    findings: list[AuditFinding] = []
    if skill.format not in {SkillFormat.SKILL_MD, SkillFormat.CLAUDE_MD, SkillFormat.CURSOR_RULES}:
        return findings

    body = skill.body or ""
    if not body:
        return findings

    line_count = len(body.splitlines())
    if line_count > LINE_WARNING_THRESHOLD:
        findings.append(
            AuditFinding(
                id="AUD-100",
                severity=Severity.LOW,
                message=(
                    f"body exceeds the recommended {LINE_WARNING_THRESHOLD}-line "
                    f"budget (got {line_count} lines)."
                ),
                file=skill.path,
                rule_kind="sizing",
                field="body",
                remediation=(
                    "Split the skill into smaller skills, or move supporting "
                    "material into a 'references/' directory."
                ),
                category="sizing",
            )
        )

    token_count = estimate_tokens(body)
    if token_count >= TOKEN_ERROR_THRESHOLD:
        findings.append(
            AuditFinding(
                id="AUD-102",
                severity=Severity.HIGH,
                message=(
                    f"body token estimate {token_count} ≥ error threshold "
                    f"{TOKEN_ERROR_THRESHOLD}; the skill is too large to load efficiently."
                ),
                file=skill.path,
                rule_kind="sizing",
                field="body",
                remediation="Split the skill; aggressively trim the body and reference long content from 'references/'.",
                category="sizing",
            )
        )
    elif token_count >= TOKEN_WARNING_THRESHOLD:
        findings.append(
            AuditFinding(
                id="AUD-101",
                severity=Severity.LOW,
                message=(
                    f"body token estimate {token_count} ≥ warn threshold "
                    f"{TOKEN_WARNING_THRESHOLD}; consider trimming."
                ),
                file=skill.path,
                rule_kind="sizing",
                field="body",
                remediation="Move supporting material into 'references/' to keep context-window cost in check.",
                category="sizing",
            )
        )

    return findings


__all__ = [
    "LINE_WARNING_THRESHOLD",
    "TOKEN_ERROR_THRESHOLD",
    "TOKEN_WARNING_THRESHOLD",
    "audit_sizing",
    "estimate_tokens",
]
