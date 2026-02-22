"""Auth Manager - Multi-login point authentication."""

import asyncio
import logging
from typing import Any

import httpx

from common.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class Session:
    """HTTP session wrapper."""

    def __init__(
        self,
        base_url: str,
        cookies: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        token: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.cookies = cookies or {}
        self.headers = headers or {}
        self.token = token
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = dict(self.headers)
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                cookies=self.cookies,
                timeout=30.0,
            )
        return self._client

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send GET request."""
        client = await self._get_client()
        return await client.get(path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Send POST request."""
        client = await self._get_client()
        return await client.post(path, **kwargs)

    async def close(self) -> None:
        """Close the session."""
        if self._client:
            await self._client.aclose()
            self._client = None


class AuthManager:
    """Manages authentication for multiple login points."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._credentials: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def set_credentials(
        self,
        login_point: str,
        username: str,
        password: str,
        **extra: Any,
    ) -> None:
        """Set credentials for a login point."""
        self._credentials[login_point] = {
            "username": username,
            "password": password,
            **extra,
        }
        logger.debug(f"Credentials set for login point: {login_point}")

    async def get_session(
        self,
        login_point: str,
        base_url: str,
        force_new: bool = False,
    ) -> Session:
        """Get or create a session for a login point."""
        async with self._lock:
            cache_key = f"{login_point}:{base_url}"

            if not force_new and cache_key in self._sessions:
                return self._sessions[cache_key]

            creds = self._credentials.get(login_point)
            if not creds:
                # Anonymous session
                session = Session(base_url=base_url)
                self._sessions[cache_key] = session
                return session

            # Authenticate and create session
            session = await self._authenticate(base_url, creds)
            self._sessions[cache_key] = session
            return session

    async def _authenticate(
        self,
        base_url: str,
        creds: dict[str, Any],
    ) -> Session:
        """Authenticate and create session."""
        login_url = creds.get("login_url", "/login")
        username = creds.get("username")
        password = creds.get("password")
        method = creds.get("method", "POST")

        async with httpx.AsyncClient(base_url=base_url) as client:
            try:
                if method.upper() == "POST":
                    response = await client.post(
                        login_url,
                        json={"username": username, "password": password},
                    )
                else:
                    response = await client.get(
                        login_url,
                        params={"username": username, "password": password},
                    )

                if response.status_code == 200:
                    # Extract token or cookies
                    token = None
                    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    token = data.get("token") or data.get("access_token")

                    session = Session(
                        base_url=base_url,
                        cookies=dict(response.cookies),
                        token=token,
                    )
                    logger.info(f"Authenticated successfully to {base_url}")
                    return session
                else:
                    logger.warning(f"Authentication failed: {response.status_code}")
                    return Session(base_url=base_url)

            except Exception as e:
                logger.error(f"Authentication error: {e}")
                return Session(base_url=base_url)

    async def invalidate_session(self, login_point: str, base_url: str) -> None:
        """Invalidate a cached session."""
        async with self._lock:
            cache_key = f"{login_point}:{base_url}"
            if cache_key in self._sessions:
                await self._sessions[cache_key].close()
                del self._sessions[cache_key]

    async def close_all(self) -> None:
        """Close all sessions."""
        async with self._lock:
            for session in self._sessions.values():
                await session.close()
            self._sessions.clear()


# Global auth manager instance
auth_manager = AuthManager()
