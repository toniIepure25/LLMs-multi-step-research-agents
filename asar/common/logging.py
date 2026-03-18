"""
Minimal logging setup shared across ASAR components.
"""

from __future__ import annotations

import logging
from typing import TextIO

from asar.common.config import LoggingSettings


LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] [trace_id=%(trace_id)s] %(message)s"


class TraceLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that injects a trace ID into every emitted record."""

    def process(self, msg: object, kwargs: dict[str, object]) -> tuple[object, dict[str, object]]:
        extra = kwargs.get("extra")
        merged_extra = dict(extra) if isinstance(extra, dict) else {}
        merged_extra.setdefault("trace_id", self.extra.get("trace_id", "-"))
        kwargs["extra"] = merged_extra
        return msg, kwargs


class TraceAwareFormatter(logging.Formatter):
    """Formatter that tolerates log records without an explicit trace ID."""

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "trace_id"):
            record.trace_id = "-"
        return super().format(record)


def setup_logging(
    settings: LoggingSettings,
    *,
    force: bool = False,
    stream: TextIO | None = None,
) -> logging.Logger:
    """Configure and return the ASAR base logger."""

    logger = logging.getLogger("asar")
    level = getattr(logging, settings.level.upper())
    logger.setLevel(level)
    logger.propagate = False

    if force:
        logger.handlers.clear()

    if not logger.handlers:
        handler = logging.StreamHandler(stream)
        handler.setLevel(level)
        handler.setFormatter(TraceAwareFormatter(LOG_FORMAT))
        logger.addHandler(handler)

    return logger


def get_logger(name: str, *, trace_id: str | None = None) -> logging.Logger | TraceLoggerAdapter:
    """Get a named ASAR logger, optionally bound to a trace ID."""

    logger = logging.getLogger(name)
    if trace_id is None:
        return logger
    return TraceLoggerAdapter(logger, {"trace_id": trace_id})
