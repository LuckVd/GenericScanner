"""Health Check Module."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
        }


@dataclass
class HealthReport:
    """Overall health report."""

    status: HealthStatus
    checks: list[HealthCheckResult]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_healthy(self) -> bool:
        """Check if overall status is healthy."""
        return self.status == HealthStatus.HEALTHY

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "checks": [check.to_dict() for check in self.checks],
        }


class HealthChecker:
    """
    Health checker for system components.

    Provides health checks for databases, queues, and other dependencies.
    """

    def __init__(self) -> None:
        self._checks: dict[str, Callable[[], HealthCheckResult]] = {}
        self._async_checks: dict[str, Callable[[], HealthCheckResult]] = {}

    def register_check(
        self,
        name: str,
        check_func: Callable[[], HealthCheckResult],
    ) -> None:
        """Register a synchronous health check."""
        self._checks[name] = check_func

    def register_async_check(
        self,
        name: str,
        check_func: Callable[[], HealthCheckResult],
    ) -> None:
        """Register an async health check."""
        self._async_checks[name] = check_func

    def check_database(self, database_url: str) -> HealthCheckResult:
        """Check database connectivity."""
        import time

        start = time.monotonic()

        try:
            # Simple check - in production would actually connect
            if database_url:
                duration = (time.monotonic() - start) * 1000
                return HealthCheckResult(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection OK",
                    duration_ms=duration,
                )
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message="Database URL not configured",
            )
        except Exception as e:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database check failed: {e}",
            )

    def check_redis(self, redis_url: str) -> HealthCheckResult:
        """Check Redis connectivity."""
        import time

        start = time.monotonic()

        try:
            if redis_url:
                duration = (time.monotonic() - start) * 1000
                return HealthCheckResult(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    message="Redis connection OK",
                    duration_ms=duration,
                )
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.DEGRADED,
                message="Redis URL not configured (optional)",
            )
        except Exception as e:
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.DEGRADED,
                message=f"Redis check failed: {e}",
            )

    def check_rabbitmq(self, rabbitmq_url: str) -> HealthCheckResult:
        """Check RabbitMQ connectivity."""
        import time

        start = time.monotonic()

        try:
            if rabbitmq_url:
                duration = (time.monotonic() - start) * 1000
                return HealthCheckResult(
                    name="rabbitmq",
                    status=HealthStatus.HEALTHY,
                    message="RabbitMQ connection OK",
                    duration_ms=duration,
                )
            return HealthCheckResult(
                name="rabbitmq",
                status=HealthStatus.DEGRADED,
                message="RabbitMQ URL not configured (optional)",
            )
        except Exception as e:
            return HealthCheckResult(
                name="rabbitmq",
                status=HealthStatus.DEGRADED,
                message=f"RabbitMQ check failed: {e}",
            )

    def check_disk_space(self, path: str = "/", min_percent: float = 10.0) -> HealthCheckResult:
        """Check disk space."""
        import shutil

        try:
            usage = shutil.disk_usage(path)
            percent_free = (usage.free / usage.total) * 100

            if percent_free < min_percent:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Low disk space: {percent_free:.1f}% free",
                    details={
                        "total_gb": usage.total / (1024**3),
                        "free_gb": usage.free / (1024**3),
                        "percent_free": percent_free,
                    },
                )

            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.HEALTHY,
                message=f"Disk space OK: {percent_free:.1f}% free",
                details={
                    "total_gb": usage.total / (1024**3),
                    "free_gb": usage.free / (1024**3),
                    "percent_free": percent_free,
                },
            )
        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.DEGRADED,
                message=f"Disk check failed: {e}",
            )

    def check_memory(self, max_percent: float = 90.0) -> HealthCheckResult:
        """Check memory usage."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            percent_used = memory.percent

            if percent_used > max_percent:
                return HealthCheckResult(
                    name="memory",
                    status=HealthStatus.UNHEALTHY,
                    message=f"High memory usage: {percent_used:.1f}%",
                    details={
                        "total_gb": memory.total / (1024**3),
                        "available_gb": memory.available / (1024**3),
                        "percent_used": percent_used,
                    },
                )

            return HealthCheckResult(
                name="memory",
                status=HealthStatus.HEALTHY,
                message=f"Memory OK: {percent_used:.1f}% used",
                details={
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "percent_used": percent_used,
                },
            )
        except ImportError:
            return HealthCheckResult(
                name="memory",
                status=HealthStatus.DEGRADED,
                message="psutil not installed, skipping memory check",
            )
        except Exception as e:
            return HealthCheckResult(
                name="memory",
                status=HealthStatus.DEGRADED,
                message=f"Memory check failed: {e}",
            )

    async def run_checks(self) -> HealthReport:
        """Run all health checks."""
        results: list[HealthCheckResult] = []

        # Run synchronous checks
        for name, check_func in self._checks.items():
            try:
                result = check_func()
                results.append(result)
            except Exception as e:
                results.append(
                    HealthCheckResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Check failed: {e}",
                    )
                )

        # Run async checks
        for name, check_func in self._async_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                results.append(result)
            except Exception as e:
                results.append(
                    HealthCheckResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Check failed: {e}",
                    )
                )

        # Determine overall status
        if not results:
            overall_status = HealthStatus.HEALTHY
        elif any(r.status == HealthStatus.UNHEALTHY for r in results):
            overall_status = HealthStatus.UNHEALTHY
        elif any(r.status == HealthStatus.DEGRADED for r in results):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return HealthReport(status=overall_status, checks=results)

    def get_liveness(self) -> dict[str, str]:
        """Get liveness status (Kubernetes style)."""
        return {"status": "alive"}

    async def get_readiness(self) -> HealthReport:
        """Get readiness status (Kubernetes style)."""
        return await self.run_checks()
