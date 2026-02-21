"""Node API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.models.node import ScanNode
from common.utils.database import get_db
from scheduler.api_gateway.schemas import NodeListResponse, NodeResponse

router = APIRouter(prefix="/api/v1/nodes", tags=["nodes"])


@router.get("", response_model=NodeListResponse)
async def list_nodes(
    db: AsyncSession = Depends(get_db),
) -> NodeListResponse:
    """Get scan node list."""
    result = await db.execute(select(ScanNode))
    nodes = result.scalars().all()

    return NodeListResponse(
        nodes=[
            NodeResponse(
                id=n.id,
                status=n.status,
                load={"cpu": n.cpu_load, "memory": n.memory_load},
                tasks_running=n.tasks_running,
                last_heartbeat=n.last_heartbeat,
            )
            for n in nodes
        ]
    )
