"""Vulnerability Detector Engine - Execute vulnerability checks."""

import asyncio
import importlib.util
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from common.models.stat import StatRecord
from common.utils.config import get_settings
from common.utils.database import get_db_context
from scanner.core_engine.auth_manager import AuthManager, Session
from scanner.core_engine.fingerprint import Fingerprint

logger = logging.getLogger(__name__)
settings = get_settings()


class VulnResult:
    """Result of a vulnerability check."""

    def __init__(
        self,
        vuln_id: str,
        target: str,
        vulnerable: bool = False,
        severity: str = "medium",
        details: dict[str, Any] | None = None,
        proof: str | None = None,
    ) -> None:
        self.vuln_id = vuln_id
        self.target = target
        self.vulnerable = vulnerable
        self.severity = severity
        self.details = details or {}
        self.proof = proof
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "vuln_id": self.vuln_id,
            "target": self.target,
            "vulnerable": self.vulnerable,
            "severity": self.severity,
            "details": self.details,
            "proof": self.proof,
            "timestamp": self.timestamp.isoformat(),
        }


class VulnCase:
    """Base class for vulnerability cases."""

    __vuln_info__: dict[str, Any] = {}

    def __init__(self, tools: dict[str, Any] | None = None) -> None:
        self.tools = tools or {}

    async def verify(
        self,
        target: str,
        session: Session,
        fingerprints: list[Fingerprint],
    ) -> VulnResult:
        """Verify if target is vulnerable. Override in subclass."""
        raise NotImplementedError

    async def cleanup(
        self,
        target: str,
        session: Session,
    ) -> None:
        """Cleanup after scan. Override in subclass."""
        pass


class VulnDetector:
    """Vulnerability detection engine."""

    def __init__(
        self,
        plugin_dir: str = "plugins/vulns",
        auth_manager: AuthManager | None = None,
    ) -> None:
        self._plugin_dir = Path(plugin_dir)
        self._cases: dict[str, type[VulnCase]] = {}
        self._case_metadata: dict[str, dict[str, Any]] = {}
        self._auth_manager = auth_manager or AuthManager()
        self._tools: dict[str, Any] = {}

        # Rate limiting
        self._rate_limiters: dict[str, asyncio.Semaphore] = {}
        self._default_rate_limit = asyncio.Semaphore(settings.scanner_rate_limit)

    def register_tool(self, name: str, tool: Any) -> None:
        """Register a tool for use by vuln cases."""
        self._tools[name] = tool

    def load_plugins(self) -> int:
        """Load all vulnerability plugins from directory."""
        if not self._plugin_dir.exists():
            logger.warning(f"Plugin directory not found: {self._plugin_dir}")
            return 0

        loaded = 0
        for py_file in self._plugin_dir.glob("**/*.py"):
            if py_file.name.startswith("_"):
                continue

            try:
                case_class = self._load_plugin(py_file)
                if case_class:
                    info = case_class.__vuln_info__
                    vuln_id = info.get("id", py_file.stem)
                    self._cases[vuln_id] = case_class
                    self._case_metadata[vuln_id] = info
                    loaded += 1
                    logger.debug(f"Loaded plugin: {vuln_id}")
            except Exception as e:
                logger.error(f"Failed to load plugin {py_file}: {e}")

        logger.info(f"Loaded {loaded} vulnerability plugins")
        return loaded

    def _load_plugin(self, path: Path) -> type[VulnCase] | None:
        """Load a single plugin file."""
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if not spec or not spec.loader:
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, VulnCase)
                and attr is not VulnCase
                and hasattr(attr, "__vuln_info__")
            ):
                return attr

        return None

    def get_matching_cases(
        self,
        fingerprints: list[Fingerprint],
        policy: str = "full",
        specified_ids: list[str] | None = None,
    ) -> list[str]:
        """Get vuln case IDs that match the given fingerprints."""
        if policy == "specified" and specified_ids:
            return [id for id in specified_ids if id in self._cases]

        matching = []
        fp_tags = set()
        fp_names = set()

        for fp in fingerprints:
            fp_tags.update(fp.tags)
            fp_names.add(fp.name.lower())

        for vuln_id, metadata in self._case_metadata.items():
            # Check policy
            if policy == "redline":
                severity = metadata.get("severity", "medium")
                if severity not in ("critical", "high"):
                    continue

            # Check fingerprint match
            fp_match = metadata.get("fingerprint", {})
            required_tags = fp_match.get("tags", [])
            required_service = fp_match.get("service", "")

            if required_tags:
                if not any(tag in fp_tags for tag in required_tags):
                    continue

            if required_service:
                if required_service.lower() not in fp_names:
                    continue

            matching.append(vuln_id)

        return matching

    async def scan_target(
        self,
        target: str,
        task_id: str,
        fingerprints: list[Fingerprint],
        case_ids: list[str],
        auth_config: dict[str, Any] | None = None,
        base_url: str | None = None,
    ) -> list[VulnResult]:
        """Scan a target with specified vuln cases."""
        results: list[VulnResult] = []

        # Get session if auth is configured
        session = None
        if auth_config and base_url:
            for login_point, creds in auth_config.items():
                self._auth_manager.set_credentials(
                    login_point,
                    creds.get("username", ""),
                    creds.get("password", ""),
                )
            session = await self._auth_manager.get_session(
                list(auth_config.keys())[0] if auth_config else "default",
                base_url,
            )

        if session is None:
            from scanner.core_engine.auth_manager import Session
            session = Session(base_url=base_url or f"http://{target}")

        for case_id in case_ids:
            if case_id not in self._cases:
                continue

            case_class = self._cases[case_id]
            case = case_class(self._tools)

            start_time = datetime.utcnow()
            status = "success"

            try:
                result = await asyncio.wait_for(
                    case.verify(target, session, fingerprints),
                    timeout=settings.scanner_default_timeout,
                )
                results.append(result)

                # Cleanup
                try:
                    await case.cleanup(target, session)
                except Exception as e:
                    logger.debug(f"Cleanup failed: {e}")

            except asyncio.TimeoutError:
                status = "timeout"
                results.append(VulnResult(
                    vuln_id=case_id,
                    target=target,
                    vulnerable=False,
                ))
            except Exception as e:
                status = "fail"
                logger.error(f"Vuln check failed {case_id} on {target}: {e}")

            # Record stat
            await self._record_stat(
                vuln_id=case_id,
                target=target,
                task_id=task_id,
                start_time=start_time,
                status=status,
            )

        return results

    async def _record_stat(
        self,
        vuln_id: str,
        target: str,
        task_id: str,
        start_time: datetime,
        status: str,
    ) -> None:
        """Record execution statistics."""
        try:
            async with get_db_context() as db:
                stat = StatRecord(
                    vuln_id=vuln_id,
                    target_id=target,
                    task_id=task_id,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    duration=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    status=status,
                )
                db.add(stat)
        except Exception as e:
            logger.error(f"Failed to record stat: {e}")


# Global vuln detector instance
vuln_detector = VulnDetector()
