"""Tests for scanner components."""

import asyncio

import pytest

from scanner.coroutine_pool import CoroutinePool
from scanner.core_engine.fingerprint import Fingerprint, FingerprintEngine
from scanner.core_engine.vuln_detector import VulnResult


class TestCoroutinePool:
    """Tests for CoroutinePool."""

    @pytest.mark.asyncio
    async def test_submit_single_task(self) -> None:
        """Test submitting a single task."""
        pool = CoroutinePool(max_size=10)

        async def simple_task() -> int:
            return 42

        task = await pool.submit(simple_task)
        result = await task
        assert result == 42
        await pool.stop()

    @pytest.mark.asyncio
    async def test_pool_limits(self) -> None:
        """Test pool concurrency limits."""
        pool = CoroutinePool(max_size=2)

        executed = []

        async def slow_task(idx: int) -> int:
            await asyncio.sleep(0.1)
            executed.append(idx)
            return idx

        # Submit 3 tasks
        tasks = []
        for i in range(3):
            task = await pool.submit(slow_task, i)
            tasks.append(task)

        # Wait for all
        await asyncio.gather(*tasks)

        assert len(executed) == 3
        await pool.stop()

    @pytest.mark.asyncio
    async def test_active_count(self) -> None:
        """Test active count tracking."""
        pool = CoroutinePool(max_size=5)

        async def blocking_task() -> None:
            await asyncio.sleep(0.2)

        # Submit tasks
        for _ in range(3):
            await pool.submit(blocking_task)

        # Check active count
        assert pool.active_count == 3
        await pool.stop()


class TestFingerprint:
    """Tests for Fingerprint."""

    def test_fingerprint_creation(self) -> None:
        """Test creating a fingerprint."""
        fp = Fingerprint(
            type="webserver",
            name="nginx",
            version="1.18.0",
            tags=["web", "proxy"],
            confidence=0.95,
        )

        assert fp.type == "webserver"
        assert fp.name == "nginx"
        assert fp.version == "1.18.0"
        assert "web" in fp.tags
        assert fp.confidence == 0.95

    def test_fingerprint_to_dict(self) -> None:
        """Test fingerprint serialization."""
        fp = Fingerprint(
            type="framework",
            name="Django",
            version="4.0",
            tags=["python", "web"],
        )

        data = fp.to_dict()

        assert data["type"] == "framework"
        assert data["name"] == "Django"
        assert data["version"] == "4.0"
        assert "python" in data["tags"]


class TestFingerprintEngine:
    """Tests for FingerprintEngine."""

    def test_load_fingerprints(self) -> None:
        """Test loading custom fingerprints."""
        engine = FingerprintEngine()

        custom_fp = {
            "name": "CustomApp",
            "type": "application",
            "patterns": [{"body": r"CustomApp"}],
        }

        engine.add_fingerprint(custom_fp)

        # Just verify it doesn't crash
        assert True

    def test_clear_cache(self) -> None:
        """Test clearing fingerprint cache."""
        engine = FingerprintEngine()
        engine._cache["http://example.com"] = []
        engine.clear_cache()
        assert len(engine._cache) == 0


class TestVulnResult:
    """Tests for VulnResult."""

    def test_result_creation(self) -> None:
        """Test creating a vuln result."""
        result = VulnResult(
            vuln_id="CVE-2023-1234",
            target="192.168.1.1",
            vulnerable=True,
            severity="high",
            details={"port": 8080},
            proof="HTTP response contained sensitive data",
        )

        assert result.vuln_id == "CVE-2023-1234"
        assert result.target == "192.168.1.1"
        assert result.vulnerable is True
        assert result.severity == "high"
        assert result.details["port"] == 8080

    def test_result_to_dict(self) -> None:
        """Test result serialization."""
        result = VulnResult(
            vuln_id="CUSTOM-001",
            target="example.com",
            vulnerable=False,
        )

        data = result.to_dict()

        assert data["vuln_id"] == "CUSTOM-001"
        assert data["target"] == "example.com"
        assert data["vulnerable"] is False
        assert "timestamp" in data

    def test_result_default_values(self) -> None:
        """Test result default values."""
        result = VulnResult(
            vuln_id="TEST-001",
            target="test.local",
        )

        assert result.vulnerable is False
        assert result.severity == "medium"
        assert result.details == {}
        assert result.proof is None
