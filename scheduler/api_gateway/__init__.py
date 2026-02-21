"""API Gateway package."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from scheduler.api_gateway.assets import router as assets_router
from scheduler.api_gateway.nodes import router as nodes_router
from scheduler.api_gateway.plugins import router as plugins_router
from scheduler.api_gateway.stats import router as stats_router
from scheduler.api_gateway.tasks import router as tasks_router


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="VulnScan Engine API",
        description="企业级分布式漏洞扫描引擎 API",
        version="0.1.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(tasks_router)
    app.include_router(assets_router)
    app.include_router(stats_router)
    app.include_router(nodes_router)
    app.include_router(plugins_router)

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.get("/")
    async def root() -> dict:
        """Root endpoint."""
        return {
            "name": "VulnScan Engine API",
            "version": "0.1.0",
            "docs": "/docs",
        }

    return app


__all__ = ["create_app"]
