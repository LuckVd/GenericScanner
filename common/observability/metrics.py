"""Prometheus Metrics Collector."""

import logging
from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class MetricValue:
    """Container for a metric value with labels."""

    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float | None = None


class Counter:
    """Prometheus counter metric."""

    def __init__(self, name: str, description: str, labels: list[str] | None = None) -> None:
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: dict[tuple, float] = defaultdict(float)

    def inc(self, value: float = 1.0, **labels: str) -> None:
        """Increment counter."""
        key = tuple(labels.get(k, "") for k in self.label_names)
        self._values[key] += value

    def get_value(self, **labels: str) -> float:
        """Get current value."""
        key = tuple(labels.get(k, "") for k in self.label_names)
        return self._values[key]

    def export(self) -> str:
        """Export in Prometheus format."""
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} counter",
        ]

        for key, value in self._values.items():
            if self.label_names and key:
                label_str = ",".join(
                    f'{k}="{v}"' for k, v in zip(self.label_names, key)
                )
                lines.append(f"{self.name}{{{label_str}}} {value}")
            else:
                lines.append(f"{self.name} {value}")

        return "\n".join(lines)


class Gauge:
    """Prometheus gauge metric."""

    def __init__(self, name: str, description: str, labels: list[str] | None = None) -> None:
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: dict[tuple, float] = defaultdict(float)

    def set(self, value: float, **labels: str) -> None:
        """Set gauge value."""
        key = tuple(labels.get(k, "") for k in self.label_names)
        self._values[key] = value

    def inc(self, value: float = 1.0, **labels: str) -> None:
        """Increment gauge."""
        key = tuple(labels.get(k, "") for k in self.label_names)
        self._values[key] += value

    def dec(self, value: float = 1.0, **labels: str) -> None:
        """Decrement gauge."""
        key = tuple(labels.get(k, "") for k in self.label_names)
        self._values[key] -= value

    def get_value(self, **labels: str) -> float:
        """Get current value."""
        key = tuple(labels.get(k, "") for k in self.label_names)
        return self._values[key]

    def export(self) -> str:
        """Export in Prometheus format."""
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} gauge",
        ]

        for key, value in self._values.items():
            if self.label_names and key:
                label_str = ",".join(
                    f'{k}="{v}"' for k, v in zip(self.label_names, key)
                )
                lines.append(f"{self.name}{{{label_str}}} {value}")
            else:
                lines.append(f"{self.name} {value}")

        return "\n".join(lines)


class Histogram:
    """Prometheus histogram metric."""

    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(
        self,
        name: str,
        description: str,
        buckets: list[float] | None = None,
        labels: list[str] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self.label_names = labels or []
        self._counts: dict[tuple, list[int]] = {}
        self._sums: dict[tuple, float] = defaultdict(float)
        self._counts_total: dict[tuple, int] = defaultdict(int)

        # Initialize bucket counts
        for key in [()]:
            self._counts[key] = [0] * len(self.buckets) + [0]  # +1 for +Inf bucket

    def observe(self, value: float, **labels: str) -> None:
        """Observe a value."""
        key = tuple(labels.get(k, "") for k in self.label_names)

        if key not in self._counts:
            self._counts[key] = [0] * len(self.buckets) + [0]

        # Update buckets
        for i, bucket in enumerate(self.buckets):
            if value <= bucket:
                self._counts[key][i] += 1
        self._counts[key][-1] += 1  # +Inf bucket

        # Update sum and count
        self._sums[key] += value
        self._counts_total[key] += 1

    def export(self) -> str:
        """Export in Prometheus format."""
        lines = [
            f"# HELP {self.name} {self.description}",
            f"# TYPE {self.name} histogram",
        ]

        for key in self._counts:
            label_prefix = ""
            if self.label_names and key:
                label_str = ",".join(
                    f'{k}="{v}"' for k, v in zip(self.label_names, key)
                )
                label_prefix = f"{{{label_str},"

            # Bucket counts
            cumulative = 0
            for i, bucket in enumerate(self.buckets):
                cumulative += self._counts[key][i]
                if label_prefix:
                    lines.append(f'{self.name}_bucket{label_prefix}le="{bucket}"}}}} {cumulative}')
                else:
                    lines.append(f'{self.name}_bucket{{{{le="{bucket}"}}}} {cumulative}')

            # +Inf bucket
            cumulative += self._counts[key][-1]
            if label_prefix:
                lines.append(f'{self.name}_bucket{label_prefix}le="+Inf"}}}} {cumulative}')
            else:
                lines.append(f'{self.name}_bucket{{{{le="+Inf"}}}} {cumulative}')

            # Sum and count
            if label_prefix:
                lines.append(f"{self.name}_sum{label_prefix[:-1]}}} {self._sums[key]}")
                lines.append(f"{self.name}_count{label_prefix[:-1]}}} {self._counts_total[key]}")
            else:
                lines.append(f"{self.name}_sum {self._sums[key]}")
                lines.append(f"{self.name}_count {self._counts_total[key]}")

        return "\n".join(lines)


class MetricsCollector:
    """
    Central metrics collector.

    Collects and exports Prometheus metrics.
    """

    def __init__(self, namespace: str = "vulnscan") -> None:
        self._namespace = namespace
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}

    def counter(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Counter:
        """Get or create a counter."""
        full_name = f"{self._namespace}_{name}"
        if full_name not in self._counters:
            self._counters[full_name] = Counter(full_name, description, labels)
        return self._counters[full_name]

    def gauge(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Gauge:
        """Get or create a gauge."""
        full_name = f"{self._namespace}_{name}"
        if full_name not in self._gauges:
            self._gauges[full_name] = Gauge(full_name, description, labels)
        return self._gauges[full_name]

    def histogram(
        self,
        name: str,
        description: str,
        buckets: list[float] | None = None,
        labels: list[str] | None = None,
    ) -> Histogram:
        """Get or create a histogram."""
        full_name = f"{self._namespace}_{name}"
        if full_name not in self._histograms:
            self._histograms[full_name] = Histogram(
                full_name, description, buckets, labels
            )
        return self._histograms[full_name]

    def export(self) -> str:
        """Export all metrics in Prometheus format."""
        parts = []

        for counter in self._counters.values():
            parts.append(counter.export())

        for gauge in self._gauges.values():
            parts.append(gauge.export())

        for histogram in self._histograms.values():
            parts.append(histogram.export())

        return "\n\n".join(parts)

    def get_stats(self) -> dict[str, Any]:
        """Get metrics statistics."""
        return {
            "namespace": self._namespace,
            "counters": len(self._counters),
            "gauges": len(self._gauges),
            "histograms": len(self._histograms),
        }


# Global metrics collector
metrics = MetricsCollector()


def setup_default_metrics() -> None:
    """Set up default application metrics."""

    # Task metrics
    metrics.counter("tasks_total", "Total number of tasks created")
    metrics.counter("tasks_completed", "Total number of tasks completed", labels=["status"])
    metrics.counter("tasks_failed", "Total number of failed tasks")

    # Scan metrics
    metrics.counter("scans_total", "Total number of scans")
    metrics.counter("vulns_found", "Total vulnerabilities found", labels=["severity"])
    metrics.histogram("scan_duration_seconds", "Scan duration in seconds")

    # Node metrics
    metrics.gauge("nodes_online", "Number of online scanner nodes")
    metrics.gauge("nodes_busy", "Number of busy scanner nodes")

    # Performance metrics
    metrics.histogram("request_duration_seconds", "Request duration in seconds")
    metrics.counter("requests_total", "Total requests", labels=["method", "endpoint", "status"])

    logger.info("Default metrics initialized")
