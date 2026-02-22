"""Structured Logging Module."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Context for trace ID
_trace_context: ContextVar[dict[str, str]] = ContextVar("trace_context", default={})


def get_log_context() -> dict[str, str]:
    """Get current logging context."""
    return _trace_context.get()


def set_log_context(**kwargs: str) -> None:
    """Set logging context values."""
    current = _trace_context.get()
    _trace_context.set({**current, **kwargs})


def clear_log_context() -> None:
    """Clear logging context."""
    _trace_context.set({})


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter."""

    def __init__(
        self,
        include_timestamp: bool = True,
        include_level: bool = True,
        include_logger: bool = True,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger = include_logger
        self.extra_fields = extra_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {}

        # Add timestamp
        if self.include_timestamp:
            log_data["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Add level
        if self.include_level:
            log_data["level"] = record.levelname.lower()

        # Add logger name
        if self.include_logger:
            log_data["logger"] = record.name

        # Add message
        log_data["message"] = record.getMessage()

        # Add context from ContextVar
        context = get_log_context()
        if context:
            log_data["context"] = context

        # Add extra fields from record
        if hasattr(record, "extra") and record.extra:
            log_data["extra"] = record.extra

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add static extra fields
        if self.extra_fields:
            log_data.update(self.extra_fields)

        return json.dumps(log_data, default=str)


class StructuredLogger:
    """
    Structured logger with context support.

    Provides methods for logging with structured data.
    """

    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
    ) -> None:
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """Internal log method."""
        record = self._logger.makeRecord(
            self._logger.name,
            level,
            "",
            0,
            message,
            (),
            None,
        )
        record.extra = kwargs  # type: ignore
        self._logger.handle(record)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)

    def with_context(self, **kwargs: Any) -> "StructuredLogger":
        """Return logger with additional context."""
        set_log_context(**{k: str(v) for k, v in kwargs.items()})
        return self


def setup_logging(
    level: str = "INFO",
    json_output: bool = True,
    include_timestamp: bool = True,
    extra_fields: dict[str, Any] | None = None,
) -> None:
    """
    Set up structured logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Whether to output JSON format
        include_timestamp: Whether to include timestamp
        extra_fields: Extra fields to include in all logs
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Set formatter
    if json_output:
        formatter = StructuredFormatter(
            include_timestamp=include_timestamp,
            extra_fields=extra_fields,
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)
