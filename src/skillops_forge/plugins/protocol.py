"""Plugin protocol — kept minimal so v1 ships only the contract."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from skillops_forge.models import Finding, SkillInventory, SkillReport


@runtime_checkable
class PluginProtocol(Protocol):
    """Hook surface available to third-party plugins."""

    name: str

    def on_inventory(self, inventory: SkillInventory) -> None:
        """Receive the inventory immediately after parsing (read-only)."""
        ...

    def on_findings(self, findings: list[Finding]) -> list[Finding] | None:
        """Optionally transform the merged findings list. Return ``None`` to keep input."""
        ...

    def on_report(self, report: SkillReport) -> SkillReport | None:
        """Optionally replace the final report. Return ``None`` to keep input."""
        ...


__all__ = ["PluginProtocol"]
