"""Distributed Tracing Module."""

import contextvars
import logging
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generator

logger = logging.getLogger(__name__)

# Context variables for trace propagation
_trace_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "trace_id", default=None
)
_span_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "span_id", default=None
)


def generate_trace_id() -> str:
    """Generate a new trace ID."""
    return uuid.uuid4().hex[:16]


def generate_span_id() -> str:
    """Generate a new span ID."""
    return uuid.uuid4().hex[:8]


def get_trace_id() -> str | None:
    """Get current trace ID."""
    return _trace_id_var.get()


def get_span_id() -> str | None:
    """Get current span ID."""
    return _span_id_var.get()


def set_trace_id(trace_id: str) -> None:
    """Set trace ID in context."""
    _trace_id_var.set(trace_id)


def set_span_id(span_id: str) -> None:
    """Set span ID in context."""
    _span_id_var.set(span_id)


@dataclass
class Span:
    """Represents a tracing span."""

    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "ok"

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
        })

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value

    def set_status(self, status: str, description: str | None = None) -> None:
        """Set span status."""
        self.status = status
        if description:
            self.attributes["status_description"] = description

    def finish(self) -> None:
        """Mark span as finished."""
        self.end_time = datetime.now(timezone.utc)

    @property
    def duration_ms(self) -> float | None:
        """Get span duration in milliseconds."""
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() * 1000
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert span to dictionary."""
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status,
        }


class TraceContext:
    """Context manager for tracing."""

    def __init__(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self._name = name
        self._attributes = attributes or {}
        self._span: Span | None = None
        self._previous_span_id: str | None = None

    def __enter__(self) -> Span:
        """Enter trace context."""
        # Get or create trace ID
        trace_id = get_trace_id()
        if not trace_id:
            trace_id = generate_trace_id()
            set_trace_id(trace_id)

        # Store previous span ID
        self._previous_span_id = get_span_id()

        # Create new span
        span_id = generate_span_id()
        self._span = Span(
            name=self._name,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=self._previous_span_id,
            attributes=self._attributes.copy(),
        )

        # Set as current span
        set_span_id(span_id)

        return self._span

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit trace context."""
        if self._span:
            if exc_type:
                self._span.set_status("error", str(exc_val))
            self._span.finish()

            # Restore previous span ID
            if self._previous_span_id:
                set_span_id(self._previous_span_id)
            else:
                _span_id_var.set(None)


class TraceManager:
    """
    Manages distributed tracing.

    Provides trace context management and span recording.
    """

    def __init__(self, service_name: str = "vulnscan-engine") -> None:
        self._service_name = service_name
        self._spans: list[Span] = []

    @contextmanager
    def trace(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> Generator[Span, None, None]:
        """Create a trace context."""
        ctx = TraceContext(name, attributes)
        span = ctx.__enter__()
        try:
            yield span
        except Exception as e:
            span.set_status("error", str(e))
            span.add_event("exception", {"type": type(e).__name__, "message": str(e)})
            raise
        finally:
            ctx.__exit__(None, None, None)
            self._spans.append(span)

    def start_trace(self, name: str, attributes: dict[str, Any] | None = None) -> TraceContext:
        """Start a new trace."""
        # Reset context for new trace
        _trace_id_var.set(None)
        _span_id_var.set(None)
        return TraceContext(name, attributes)

    def get_current_trace_id(self) -> str | None:
        """Get current trace ID."""
        return get_trace_id()

    def get_current_span_id(self) -> str | None:
        """Get current span ID."""
        return get_span_id()

    def get_spans(self) -> list[dict[str, Any]]:
        """Get all recorded spans."""
        return [span.to_dict() for span in self._spans]

    def clear_spans(self) -> None:
        """Clear recorded spans."""
        self._spans.clear()

    def export_trace(self) -> dict[str, Any]:
        """Export trace data."""
        return {
            "service_name": self._service_name,
            "spans": self.get_spans(),
            "span_count": len(self._spans),
        }


# Global trace manager
trace_manager = TraceManager()


def trace(name: str, attributes: dict[str, Any] | None = None) -> TraceContext:
    """Create a trace context."""
    return TraceContext(name, attributes)
