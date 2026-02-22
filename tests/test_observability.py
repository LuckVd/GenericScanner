"""Tests for Observability module."""

import json
import logging
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from common.observability import (
    HealthChecker,
    HealthStatus,
    MetricsCollector,
    StructuredLogger,
    TraceContext,
    TraceManager,
    get_trace_id,
    metrics,
    setup_logging,
    setup_default_metrics,
)


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    def test_create_collector(self) -> None:
        """Test creating a metrics collector."""
        collector = MetricsCollector(namespace="test")
        assert collector is not None
        assert collector._namespace == "test"

    def test_create_counter(self) -> None:
        """Test creating a counter."""
        collector = MetricsCollector(namespace="test")
        counter = collector.counter("requests", "Total requests")

        counter.inc()
        assert counter.get_value() == 1.0

        counter.inc(5)
        assert counter.get_value() == 6.0

    def test_counter_with_labels(self) -> None:
        """Test counter with labels."""
        collector = MetricsCollector(namespace="test")
        counter = collector.counter(
            "http_requests",
            "HTTP requests",
            labels=["method", "status"],
        )

        counter.inc(method="GET", status="200")
        counter.inc(method="GET", status="200")
        counter.inc(method="POST", status="201")

        assert counter.get_value(method="GET", status="200") == 2.0
        assert counter.get_value(method="POST", status="201") == 1.0

    def test_create_gauge(self) -> None:
        """Test creating a gauge."""
        collector = MetricsCollector(namespace="test")
        gauge = collector.gauge("temperature", "Current temperature")

        gauge.set(25.5)
        assert gauge.get_value() == 25.5

        gauge.inc(2.0)
        assert gauge.get_value() == 27.5

        gauge.dec(5.0)
        assert gauge.get_value() == 22.5

    def test_create_histogram(self) -> None:
        """Test creating a histogram."""
        collector = MetricsCollector(namespace="test")
        histogram = collector.histogram(
            "request_duration",
            "Request duration in seconds",
        )

        histogram.observe(0.1)
        histogram.observe(0.5)
        histogram.observe(1.5)

        # Export should contain bucket counts
        exported = histogram.export()
        assert "request_duration" in exported
        assert "le=" in exported

    def test_export_metrics(self) -> None:
        """Test exporting all metrics."""
        collector = MetricsCollector(namespace="test")

        counter = collector.counter("total", "Total count")
        counter.inc(10)

        gauge = collector.gauge("current", "Current value")
        gauge.set(5)

        exported = collector.export()

        assert "test_total" in exported
        assert "test_current" in exported
        assert "# TYPE test_total counter" in exported
        assert "# TYPE test_current gauge" in exported

    def test_get_stats(self) -> None:
        """Test getting collector stats."""
        collector = MetricsCollector(namespace="test")

        collector.counter("c1", "Counter 1")
        collector.gauge("g1", "Gauge 1")
        collector.histogram("h1", "Histogram 1")

        stats = collector.get_stats()

        assert stats["namespace"] == "test"
        assert stats["counters"] == 1
        assert stats["gauges"] == 1
        assert stats["histograms"] == 1

    def test_global_metrics(self) -> None:
        """Test global metrics instance."""
        assert metrics is not None
        assert isinstance(metrics, MetricsCollector)

    def test_setup_default_metrics(self) -> None:
        """Test setting up default metrics."""
        setup_default_metrics()

        # Should have created standard metrics
        stats = metrics.get_stats()
        assert stats["counters"] > 0
        assert stats["gauges"] > 0
        assert stats["histograms"] > 0


class TestStructuredLogging:
    """Tests for structured logging."""

    def test_structured_formatter(self) -> None:
        """Test structured JSON formatter."""
        from common.observability.logging import StructuredFormatter

        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "info"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data

    def test_structured_logger(self) -> None:
        """Test structured logger."""
        logger = StructuredLogger("test.logger")

        assert logger is not None
        assert logger._logger.name == "test.logger"

    def test_log_context(self) -> None:
        """Test log context management."""
        from common.observability.logging import (
            set_log_context,
            clear_log_context,
            get_log_context,
        )

        set_log_context(trace_id="abc123", user_id="user1")

        context = get_log_context()
        assert context["trace_id"] == "abc123"
        assert context["user_id"] == "user1"

        clear_log_context()
        context = get_log_context()
        assert context == {}

    def test_setup_logging_json(self) -> None:
        """Test setting up JSON logging."""
        # Capture stdout
        import sys
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            setup_logging(level="DEBUG", json_output=True)

            test_logger = logging.getLogger("test.json")
            test_logger.info("Test JSON log")

            output = sys.stdout.getvalue()
            # Should be valid JSON
            if output.strip():
                data = json.loads(output.strip())
                assert "message" in data
        finally:
            sys.stdout = old_stdout


class TestTracing:
    """Tests for distributed tracing."""

    def test_generate_trace_id(self) -> None:
        """Test trace ID generation."""
        from common.observability.tracing import generate_trace_id

        trace_id = generate_trace_id()
        assert len(trace_id) == 16
        assert trace_id.isalnum()

        # Should be unique
        trace_id2 = generate_trace_id()
        assert trace_id != trace_id2

    def test_generate_span_id(self) -> None:
        """Test span ID generation."""
        from common.observability.tracing import generate_span_id

        span_id = generate_span_id()
        assert len(span_id) == 8
        assert span_id.isalnum()

    def test_trace_context(self) -> None:
        """Test trace context."""
        ctx = TraceContext("test_operation")

        with ctx as span:
            assert span.name == "test_operation"
            assert span.trace_id is not None
            assert span.span_id is not None
            assert span.status == "ok"

        # Span should be finished
        assert span.end_time is not None
        assert span.duration_ms is not None

    def test_trace_context_with_error(self) -> None:
        """Test trace context with error."""
        ctx = TraceContext("failing_operation")

        try:
            with ctx as span:
                raise ValueError("Test error")
        except ValueError:
            pass

        # Span should have error status
        assert span.status == "error"

    def test_span_attributes(self) -> None:
        """Test span attributes and events."""
        ctx = TraceContext("test", attributes={"key": "value"})

        with ctx as span:
            span.set_attribute("custom", "data")
            span.add_event("something_happened", {"detail": "info"})

        assert span.attributes["key"] == "value"
        assert span.attributes["custom"] == "data"
        assert len(span.events) == 1
        assert span.events[0]["name"] == "something_happened"

    def test_span_to_dict(self) -> None:
        """Test span serialization."""
        ctx = TraceContext("test")

        with ctx as span:
            pass

        data = span.to_dict()

        assert data["name"] == "test"
        assert "trace_id" in data
        assert "span_id" in data
        assert "start_time" in data
        assert "duration_ms" in data

    def test_trace_manager(self) -> None:
        """Test trace manager."""
        manager = TraceManager(service_name="test-service")

        with manager.trace("operation1"):
            pass

        with manager.trace("operation2"):
            pass

        spans = manager.get_spans()
        assert len(spans) == 2

        export = manager.export_trace()
        assert export["service_name"] == "test-service"
        assert export["span_count"] == 2

        manager.clear_spans()
        assert len(manager.get_spans()) == 0

    def test_get_trace_id(self) -> None:
        """Test getting trace ID from context."""
        ctx = TraceContext("test")

        with ctx:
            current_id = get_trace_id()
            assert current_id is not None
            assert len(current_id) == 16


class TestHealthChecker:
    """Tests for health checker."""

    @pytest.fixture
    def health_checker(self) -> HealthChecker:
        """Create health checker instance."""
        return HealthChecker()

    def test_create_health_checker(self, health_checker: HealthChecker) -> None:
        """Test creating health checker."""
        assert health_checker is not None

    def test_check_database(self, health_checker: HealthChecker) -> None:
        """Test database health check."""
        result = health_checker.check_database("mysql://localhost/test")

        assert result.name == "database"
        assert result.status == HealthStatus.HEALTHY

    def test_check_database_no_url(self, health_checker: HealthChecker) -> None:
        """Test database check without URL."""
        result = health_checker.check_database("")

        assert result.name == "database"
        assert result.status == HealthStatus.UNHEALTHY

    def test_check_redis(self, health_checker: HealthChecker) -> None:
        """Test Redis health check."""
        result = health_checker.check_redis("redis://localhost")

        assert result.name == "redis"
        assert result.status == HealthStatus.HEALTHY

    def test_check_redis_no_url(self, health_checker: HealthChecker) -> None:
        """Test Redis check without URL."""
        result = health_checker.check_redis("")

        assert result.name == "redis"
        assert result.status == HealthStatus.DEGRADED

    def test_check_rabbitmq(self, health_checker: HealthChecker) -> None:
        """Test RabbitMQ health check."""
        result = health_checker.check_rabbitmq("amqp://localhost")

        assert result.name == "rabbitmq"
        assert result.status == HealthStatus.HEALTHY

    def test_check_disk_space(self, health_checker: HealthChecker) -> None:
        """Test disk space check."""
        result = health_checker.check_disk_space()

        assert result.name == "disk_space"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY]
        assert "percent_free" in result.details

    def test_register_custom_check(self, health_checker: HealthChecker) -> None:
        """Test registering custom health check."""

        def custom_check() -> "HealthCheckResult":
            from common.observability.health import HealthCheckResult
            return HealthCheckResult(
                name="custom",
                status=HealthStatus.HEALTHY,
                message="Custom check passed",
            )

        health_checker.register_check("custom", custom_check)

    @pytest.mark.asyncio
    async def test_run_checks(self, health_checker: HealthChecker) -> None:
        """Test running all health checks."""
        report = await health_checker.run_checks()

        assert report.status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
        ]
        assert report.timestamp is not None
        assert isinstance(report.checks, list)

    def test_get_liveness(self, health_checker: HealthChecker) -> None:
        """Test liveness endpoint."""
        liveness = health_checker.get_liveness()

        assert liveness["status"] == "alive"

    @pytest.mark.asyncio
    async def test_get_readiness(self, health_checker: HealthChecker) -> None:
        """Test readiness endpoint."""
        readiness = await health_checker.get_readiness()

        assert readiness.status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
        ]

    def test_health_report_to_dict(self, health_checker: HealthChecker) -> None:
        """Test health report serialization."""
        from common.observability.health import HealthReport, HealthCheckResult

        report = HealthReport(
            status=HealthStatus.HEALTHY,
            checks=[
                HealthCheckResult(
                    name="test",
                    status=HealthStatus.HEALTHY,
                    message="OK",
                )
            ],
        )

        data = report.to_dict()

        assert data["status"] == "healthy"
        assert len(data["checks"]) == 1
        assert data["checks"][0]["name"] == "test"

    def test_health_check_result_to_dict(self) -> None:
        """Test health check result serialization."""
        from common.observability.health import HealthCheckResult

        result = HealthCheckResult(
            name="test",
            status=HealthStatus.HEALTHY,
            message="All good",
            details={"key": "value"},
            duration_ms=1.5,
        )

        data = result.to_dict()

        assert data["name"] == "test"
        assert data["status"] == "healthy"
        assert data["message"] == "All good"
        assert data["details"]["key"] == "value"
        assert data["duration_ms"] == 1.5
