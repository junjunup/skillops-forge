"""Security scanner — orchestrates rule loading and matching."""

from __future__ import annotations

from pathlib import Path

from skillops_forge.models import SecurityFinding, SkillInventory
from skillops_forge.scanner.engine import ScannerEngine

_default_engine: ScannerEngine | None = None


def _get_engine() -> ScannerEngine:
    global _default_engine
    if _default_engine is None:
        _default_engine = ScannerEngine.from_builtins()
    return _default_engine


def run_scan(
    inventory: SkillInventory,
    *,
    rule_dirs: list[Path] | None = None,
) -> list[SecurityFinding]:
    """Run all loaded rules over every file in ``inventory``.

    Args:
        inventory: Inventory to scan.
        rule_dirs: Optional override; when None, the bundled rules are used.

    Returns:
        A flat list of :class:`SecurityFinding` instances (possibly empty).
    """
    engine = ScannerEngine.from_dirs(rule_dirs) if rule_dirs else _get_engine()
    findings: list[SecurityFinding] = []
    for skill in inventory.files:
        findings.extend(engine.scan(skill))
    return findings


__all__ = ["ScannerEngine", "run_scan"]
