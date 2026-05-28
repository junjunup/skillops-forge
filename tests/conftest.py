"""Shared pytest fixtures for SkillOps Forge."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def fixtures_root() -> Path:
    """Return the absolute path to the tests/fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def good_root(fixtures_root: Path) -> Path:
    return fixtures_root / "good"


@pytest.fixture(scope="session")
def bad_root(fixtures_root: Path) -> Path:
    return fixtures_root / "bad"
