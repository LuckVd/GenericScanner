"""Plugin API routes."""

from fastapi import APIRouter

from scheduler.api_gateway.schemas import PluginListResponse, PluginReloadResponse

router = APIRouter(prefix="/api/v1/plugins", tags=["plugins"])


@router.get("", response_model=PluginListResponse)
async def list_plugins(
    type: str = None,
) -> PluginListResponse:
    """Get plugin list."""
    # TODO: Implement actual plugin listing from plugin_repo
    return PluginListResponse(plugins=[])


@router.post("/reload", response_model=PluginReloadResponse)
async def reload_plugins() -> PluginReloadResponse:
    """Reload all plugins."""
    # TODO: Implement actual plugin reload
    return PluginReloadResponse(
        message="Plugins reloaded successfully",
        count=0,
    )
