"""Structured logging configuration using structlog.

Runs in stdlib integration mode — existing ``logging.getLogger`` calls
continue to work and gain structlog processing automatically.  New code
should use ``get_logger(__name__)`` for structured key-value logging.

Toggle output format via ``AXON_LOG_FORMAT``:
- ``"console"`` (default) — coloured, human-readable
- ``"json"`` — one JSON object per line (production / log aggregators)
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(*, level: str = "INFO", log_format: str = "console") -> None:
    """Set up structlog + stdlib logging.

    Call once at startup (before any logger is used).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Shared processors applied to every log event
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_format == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    # Configure structlog to wrap stdlib
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib root handler so *all* loggers (including third-party
    # and not-yet-migrated modules) emit through the structlog pipeline.
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(numeric_level)

    # Keep memory pipeline at the configured level (may diverge later)
    for module in (
        "axon.vault.memory_manager",
        "axon.vault.memory_recall",
        "axon.vault.memory_learning",
        "axon.vault.memory_prompts",
        "axon.agents.agent",
    ):
        logging.getLogger(module).setLevel(numeric_level)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog bound logger for *name*.

    Preferred over ``logging.getLogger`` for new/migrated code.
    """
    return structlog.stdlib.get_logger(name)
