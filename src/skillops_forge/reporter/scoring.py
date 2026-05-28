"""Risk-weighted scoring (architecture §7).

* Total deductions = sum(severity_weight * count).
* Score = max(0, 100 - deductions).
* Overall risk uses CRITICAL > HIGH > MEDIUM > LOW > INFO precedence.
* A single CRITICAL finding always sets ``passed = False``.
"""

from __future__ import annotations

from collections.abc import Iterable

from skillops_forge.config import SEVERITY_WEIGHTS
from skillops_forge.models import Finding, Severity


def calculate_score(findings: Iterable[Finding]) -> tuple[int, Severity]:
    """Return ``(score, overall_risk)`` for a flat iterable of findings.

    The function is pure and stable; identical inputs yield identical outputs.
    """
    counts = {s.value: 0 for s in Severity}
    for f in findings:
        counts[f.severity.value] = counts.get(f.severity.value, 0) + 1
    deductions = sum(
        SEVERITY_WEIGHTS.get(name, 0) * counts.get(name, 0) for name in SEVERITY_WEIGHTS
    )
    score = max(0, 100 - deductions)
    risk = _overall_risk(counts)
    return score, risk


def is_passed(score: int, threshold: int, has_critical: bool) -> bool:
    """Return True only when score meets threshold AND no CRITICAL is present."""
    if has_critical:
        return False
    return score >= threshold


def _overall_risk(counts: dict[str, int]) -> Severity:
    if counts.get("critical", 0) >= 1:
        return Severity.CRITICAL
    if counts.get("high", 0) >= 2:
        return Severity.HIGH
    if counts.get("high", 0) == 1:
        return Severity.MEDIUM
    if counts.get("medium", 0) >= 3:
        return Severity.MEDIUM
    if counts.get("medium", 0) >= 1:
        return Severity.LOW
    return Severity.INFO


__all__ = ["calculate_score", "is_passed"]
