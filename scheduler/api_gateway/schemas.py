"""Pydantic schemas for API request/response."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# Task schemas
class TaskCreate(BaseModel):
    """Task creation request."""

    name: str = Field(..., description="Task name")
    targets: list[str] = Field(..., description="Target list (IPs, domains, CIDR)")
    auth: dict[str, Any] | None = Field(None, description="Authentication info")
    policy: str = Field("full", description="Scan policy")
    vuln_ids: list[str] | None = Field(None, description="Specific vuln IDs")
    priority: int = Field(5, ge=1, le=10, description="Priority (1-10)")
    options: dict[str, Any] | None = Field(None, description="Scan options")


class TaskResponse(BaseModel):
    """Task response."""

    id: str
    name: str
    status: str
    progress: dict[str, int]
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class TaskDetailResponse(BaseModel):
    """Task detail response."""

    id: str
    name: str
    targets: list[str]
    auth: dict[str, Any] | None = None
    policy: str
    vuln_ids: list[str] | None = None
    priority: int
    options: dict[str, Any] | None = None
    status: str
    progress: dict[str, int]
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Task list response."""

    total: int
    page: int
    size: int
    items: list[TaskResponse]


class TaskPauseResponse(BaseModel):
    """Task pause response."""

    id: str
    status: str
    message: str


class TaskResumeResponse(BaseModel):
    """Task resume response."""

    id: str
    status: str
    message: str


class TaskResultResponse(BaseModel):
    """Task scan results response."""

    task_id: str
    total_vulns: int
    by_severity: dict[str, int]
    results: list[dict[str, Any]]


# Asset schemas
class AssetListResponse(BaseModel):
    """Asset list response."""

    total: int
    page: int
    size: int
    items: list[dict[str, Any]]


class AssetDetailResponse(BaseModel):
    """Asset detail response."""

    id: str
    ip: str | None = None
    domain: str | None = None
    ports: list[int]
    services: list[dict[str, Any]]
    fingerprints: list[dict[str, Any]]
    tags: list[str]
    last_scan: datetime | None = None

    class Config:
        from_attributes = True


class AssetTagsUpdate(BaseModel):
    """Asset tags update request."""

    add: list[str] | None = Field(None, description="Tags to add")
    remove: list[str] | None = Field(None, description="Tags to remove")


# Stats schemas
class StatsOverviewResponse(BaseModel):
    """Stats overview response."""

    total_tasks: int
    total_assets: int
    total_vulns: int
    by_severity: dict[str, int]


class VulnStatsResponse(BaseModel):
    """Vuln statistics response."""

    vuln_id: str
    total_executions: int
    success_rate: float
    vuln_found_rate: float
    avg_duration: int


# Node schemas
class NodeResponse(BaseModel):
    """Node response."""

    id: str
    status: str
    load: dict[str, float | None]
    tasks_running: int
    last_heartbeat: datetime | None = None

    class Config:
        from_attributes = True


class NodeListResponse(BaseModel):
    """Node list response."""

    nodes: list[NodeResponse]


# Plugin schemas
class PluginResponse(BaseModel):
    """Plugin response."""

    id: str
    name: str
    severity: str
    tags: list[str]
    enabled: bool
    md5: str | None = None

    class Config:
        from_attributes = True


class PluginListResponse(BaseModel):
    """Plugin list response."""

    plugins: list[PluginResponse]


class PluginReloadResponse(BaseModel):
    """Plugin reload response."""

    message: str
    count: int


# Error response
class ErrorResponse(BaseModel):
    """Error response."""

    error: dict[str, Any]
