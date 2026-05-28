"""Global configuration constants for SkillOps Forge.

Per the product strategy lock-in (2026-05-25, Q1-Q10):

* Q1 default report directory: ``./reports/``
* Q2 default threshold: ``70``
* Q3 severity weights: critical=25 / high=12 / medium=5 / low=2
* Q4 a single CRITICAL finding is a hard veto regardless of score
* Q5 ``.cursor/rules`` is included by default (``--no-cursor-rules`` to opt out)
* Q6 examples dry-run is on by default (``--no-runner`` to opt out)
* Q7 ``init-ci`` refuses to overwrite without ``--force``
* Q9 GitHub Actions template MUST pin to ``actions/checkout@v4`` +
  ``actions/setup-python@v5``
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

# ---------------------------------------------------------------------------
# CLI exit codes
# ---------------------------------------------------------------------------
EXIT_OK: Final[int] = 0
EXIT_AUDIT_FAILED: Final[int] = 1
EXIT_USER_ERROR: Final[int] = 2
EXIT_INTERNAL_ERROR: Final[int] = 3

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_THRESHOLD: Final[int] = 70
DEFAULT_OUT_DIR: Final[Path] = Path("reports")

REPORT_FILENAMES: Final[dict[str, str]] = {
    "md": "skillops-report.md",
    "html": "skillops-report.html",
    "json": "skillops-result.json",
}

# Severity weights (Q3) — keyed by lowercase severity name.
SEVERITY_WEIGHTS: Final[dict[str, int]] = {
    "critical": 25,
    "high": 12,
    "medium": 5,
    "low": 2,
    "info": 0,
}

# Severity color palette for HTML reports (architecture §8.3).
SEVERITY_COLORS: Final[dict[str, str]] = {
    "critical": "#D7263D",
    "high": "#F46036",
    "medium": "#F4C430",
    "low": "#A0A0A0",
    "info": "#5C8DB7",
}

# Default GitHub Actions pinned versions (Q9).
GH_ACTIONS_CHECKOUT_REF: Final[str] = "actions/checkout@v4"
GH_ACTIONS_SETUP_PYTHON_REF: Final[str] = "actions/setup-python@v5"

# Allowlist of domains that are NOT flagged by SEC-010.
EXFIL_ALLOWED_DOMAINS: Final[tuple[str, ...]] = (
    "github.com",
    "raw.githubusercontent.com",
    "pypi.org",
    "files.pythonhosted.org",
    "docs.python.org",
)

# Heuristic thresholds used by the scanner.
BASE64_LINE_LENGTH_THRESHOLD: Final[int] = 120
ENTROPY_THRESHOLD: Final[float] = 4.5
ZERO_WIDTH_CHARS: Final[str] = "\u200b\u200c\u200d\u2060\ufeff"

# ---------------------------------------------------------------------------
# Rule documentation base URL — every finding's docs_url is built from this.
# When the project is hosted at a different repo, override via env or CLI flag
# in a future release. For 0.2 we hardcode the canonical path.
# ---------------------------------------------------------------------------
DOCS_BASE_URL: Final[str] = "https://github.com/junjunup/skillops-forge/blob/main/docs/rules"


def docs_url_for(rule_id: str) -> str:
    """Return the canonical documentation URL for ``rule_id`` (e.g. SEC-012)."""
    return f"{DOCS_BASE_URL}/{rule_id}.md"
