"""Logging configuration with optional Rich formatting."""

from __future__ import annotations

import logging
from typing import Final

from rich.logging import RichHandler

_LOGGER_NAME: Final[str] = "skillops_forge"
_DEFAULT_FMT: Final[str] = "%(message)s"


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure root logger for ``skillops_forge`` and return it.

    Calling this function multiple times is safe; the handler is reset.

    Args:
        verbose: If True, the log level is DEBUG; otherwise INFO.

    Returns:
        The configured ``skillops_forge`` package logger.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    level = logging.DEBUG if verbose else logging.INFO

    # Reset handlers to avoid duplicate output across repeated calls.
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    handler = RichHandler(
        rich_tracebacks=True,
        markup=False,
        show_path=verbose,
        show_time=False,
        show_level=True,
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_DEFAULT_FMT))

    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_logger() -> logging.Logger:
    """Return the package logger (configured or not)."""
    return logging.getLogger(_LOGGER_NAME)
