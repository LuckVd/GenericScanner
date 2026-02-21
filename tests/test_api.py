"""Tests for API endpoints."""

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient) -> None:
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient) -> None:
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


class TestTaskAPI:
    """Tests for task API endpoints."""

    @pytest.mark.asyncio
    async def test_create_task(self, client: AsyncClient) -> None:
        """Test creating a task."""
        task_data = {
            "name": "Test Scan",
            "targets": ["192.168.1.1"],
            "policy": "full",
            "priority": 5,
        }

        response = await client.post("/api/v1/tasks", json=task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Scan"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_tasks(self, client: AsyncClient) -> None:
        """Test listing tasks."""
        response = await client.get("/api/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, client: AsyncClient) -> None:
        """Test getting non-existent task."""
        response = await client.get("/api/v1/tasks/non-existent-id")
        assert response.status_code == 404


class TestAssetAPI:
    """Tests for asset API endpoints."""

    @pytest.mark.asyncio
    async def test_list_assets(self, client: AsyncClient) -> None:
        """Test listing assets."""
        response = await client.get("/api/v1/assets")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_asset_not_found(self, client: AsyncClient) -> None:
        """Test getting non-existent asset."""
        response = await client.get("/api/v1/assets/non-existent-id")
        assert response.status_code == 404


class TestStatsAPI:
    """Tests for stats API endpoints."""

    @pytest.mark.asyncio
    async def test_stats_overview(self, client: AsyncClient) -> None:
        """Test stats overview endpoint."""
        response = await client.get("/api/v1/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "total_assets" in data
        assert "total_vulns" in data


class TestNodeAPI:
    """Tests for node API endpoints."""

    @pytest.mark.asyncio
    async def test_list_nodes(self, client: AsyncClient) -> None:
        """Test listing nodes."""
        response = await client.get("/api/v1/nodes")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data


class TestPluginAPI:
    """Tests for plugin API endpoints."""

    @pytest.mark.asyncio
    async def test_list_plugins(self, client: AsyncClient) -> None:
        """Test listing plugins."""
        response = await client.get("/api/v1/plugins")
        assert response.status_code == 200
        data = response.json()
        assert "plugins" in data

    @pytest.mark.asyncio
    async def test_reload_plugins(self, client: AsyncClient) -> None:
        """Test reloading plugins."""
        response = await client.post("/api/v1/plugins/reload")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "count" in data
