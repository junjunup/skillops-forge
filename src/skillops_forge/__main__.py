"""Entry point for ``python -m skillops_forge``."""

from __future__ import annotations

from skillops_forge.cli import app


def main() -> None:
    """Invoke the typer CLI."""
    app()


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
