"""Abstract base parser."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from skillops_forge.models import SkillFile


class BaseParser(ABC):
    """ABC for skill source parsers."""

    suffixes: tuple[str, ...] = (".md",)

    def can_handle(self, path: Path) -> bool:
        """Return True when this parser is able to parse ``path``.

        Default impl matches by suffix; subclasses may override for stricter rules.
        """
        return path.suffix.lower() in self.suffixes

    @abstractmethod
    def parse(self, path: Path) -> SkillFile:
        """Parse ``path`` into a :class:`SkillFile`. Raises :class:`ParseError`."""

    @staticmethod
    def read_text(path: Path) -> str:
        """Read file with utf-8-sig to tolerate BOM-prefixed files."""
        return path.read_text(encoding="utf-8-sig")
