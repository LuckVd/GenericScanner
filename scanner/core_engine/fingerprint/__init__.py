"""Fingerprint Engine - Service and web fingerprint identification."""

import asyncio
import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class Fingerprint:
    """Represents a detected fingerprint."""

    def __init__(
        self,
        type: str,
        name: str,
        version: str | None = None,
        tags: list[str] | None = None,
        confidence: float = 1.0,
    ) -> None:
        self.type = type  # web, service, os
        self.name = name
        self.version = version
        self.tags = tags or []
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "name": self.name,
            "version": self.version,
            "tags": self.tags,
            "confidence": self.confidence,
        }


# Built-in web fingerprints
WEB_FINGERPRINTS = [
    # Web servers
    {
        "name": "nginx",
        "type": "webserver",
        "patterns": [
            {"header": "Server", "regex": r"nginx[/\s]*([\d.]+)?"},
        ],
    },
    {
        "name": "Apache",
        "type": "webserver",
        "patterns": [
            {"header": "Server", "regex": r"Apache[/\s]*([\d.]+)?"},
        ],
    },
    {
        "name": "IIS",
        "type": "webserver",
        "patterns": [
            {"header": "Server", "regex": r"Microsoft-IIS[/\s]*([\d.]+)?"},
        ],
    },
    # Frameworks
    {
        "name": "Django",
        "type": "framework",
        "patterns": [
            {"header": "Set-Cookie", "regex": r"csrftoken"},
            {"body": r"csrfmiddlewaretoken"},
        ],
    },
    {
        "name": "Flask",
        "type": "framework",
        "patterns": [
            {"cookie": r"session=.*\."},
        ],
    },
    {
        "name": "Spring",
        "type": "framework",
        "patterns": [
            {"header": "Set-Cookie", "regex": r"JSESSIONID"},
        ],
    },
    # Applications
    {
        "name": "WordPress",
        "type": "cms",
        "patterns": [
            {"body": r"wp-content"},
            {"body": r"WordPress"},
            {"path": "/wp-login.php", "status": 200},
        ],
    },
    {
        "name": "Tomcat",
        "type": "server",
        "patterns": [
            {"body": r"Apache Tomcat"},
            {"path": "/manager/html", "status": [200, 401]},
        ],
        "tags": ["manager"],
    },
    {
        "name": "phpMyAdmin",
        "type": "database",
        "patterns": [
            {"body": r"phpMyAdmin"},
            {"path": "/phpmyadmin/", "status": 200},
        ],
    },
    {
        "name": "Jenkins",
        "type": "ci",
        "patterns": [
            {"header": "X-Jenkins", "regex": r"([\d.]+)"},
        ],
    },
    {
        "name": "GitLab",
        "type": "vcs",
        "patterns": [
            {"body": r"GitLab"},
        ],
    },
]


class FingerprintEngine:
    """Engine for fingerprint identification."""

    def __init__(self) -> None:
        self._web_fingerprints = WEB_FINGERPRINTS
        self._cache: dict[str, list[Fingerprint]] = {}
        self._custom_fingerprints: list[dict[str, Any]] = []

    def add_fingerprint(self, fingerprint: dict[str, Any]) -> None:
        """Add a custom fingerprint."""
        self._custom_fingerprints.append(fingerprint)

    def load_fingerprints(self, fingerprints: list[dict[str, Any]]) -> None:
        """Load fingerprints from list."""
        for fp in fingerprints:
            self.add_fingerprint(fp)

    async def identify(
        self,
        target: str,
        port: int | None = None,
        use_cache: bool = True,
    ) -> list[Fingerprint]:
        """Identify fingerprints for a target."""
        # Build URL
        scheme = "https" if port == 443 else "http"
        if port and port not in (80, 443):
            url = f"{scheme}://{target}:{port}"
        else:
            url = f"{scheme}://{target}"

        # Check cache
        if use_cache and url in self._cache:
            return self._cache[url]

        fingerprints: list[Fingerprint] = []

        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                # Get main page
                response = await client.get(url, follow_redirects=True)

                # Identify from response
                web_fps = await self._identify_web(response, client, url)
                fingerprints.extend(web_fps)

        except Exception as e:
            logger.debug(f"Fingerprint identification failed for {url}: {e}")

        # Cache results
        self._cache[url] = fingerprints
        return fingerprints

    async def _identify_web(
        self,
        response: httpx.Response,
        client: httpx.AsyncClient,
        base_url: str,
    ) -> list[Fingerprint]:
        """Identify web fingerprints from response."""
        fingerprints: list[Fingerprint] = []
        headers = dict(response.headers)
        body = response.text

        all_fps = self._web_fingerprints + self._custom_fingerprints

        for fp_def in all_fps:
            name = fp_def.get("name", "unknown")
            fp_type = fp_def.get("type", "unknown")
            patterns = fp_def.get("patterns", [])
            tags = fp_def.get("tags", [])

            version = None
            matched = False

            for pattern in patterns:
                # Header pattern
                if "header" in pattern:
                    header_name = pattern["header"]
                    header_value = headers.get(header_name, "")
                    regex = pattern.get("regex", r".*")
                    match = re.search(regex, header_value, re.IGNORECASE)
                    if match:
                        matched = True
                        if match.groups():
                            version = match.group(1)

                # Body pattern
                elif "body" in pattern:
                    regex = pattern["body"]
                    if re.search(regex, body, re.IGNORECASE):
                        matched = True

                # Path pattern
                elif "path" in pattern:
                    path = pattern["path"]
                    expected_status = pattern.get("status", 200)
                    if isinstance(expected_status, int):
                        expected_status = [expected_status]

                    try:
                        check_response = await client.get(f"{base_url}{path}")
                        if check_response.status_code in expected_status:
                            matched = True
                    except Exception:
                        pass

                # Cookie pattern
                elif "cookie" in pattern:
                    cookies = response.cookies
                    cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
                    regex = pattern["cookie"]
                    if re.search(regex, cookie_str):
                        matched = True

                if matched:
                    break

            if matched:
                fingerprints.append(Fingerprint(
                    type=fp_type,
                    name=name,
                    version=version,
                    tags=tags,
                ))

        return fingerprints

    def clear_cache(self) -> None:
        """Clear the fingerprint cache."""
        self._cache.clear()


# Global fingerprint engine instance
fingerprint_engine = FingerprintEngine()
