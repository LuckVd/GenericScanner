"""Stats API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.models.stat import StatRecord
from common.models.target import Target
from common.models.task import Task
from common.utils.database import get_db
from scheduler.api_gateway.schemas import StatsOverviewResponse

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("/overview", response_model=StatsOverviewResponse)
async def get_stats_overview(
    db: AsyncSession = Depends(get_db),
) -> StatsOverviewResponse:
    """Get statistics overview."""
    # Count tasks
    tasks_result = await db.execute(select(func.count()).select_from(Task))
    total_tasks = tasks_result.scalar() or 0

    # Count assets
    assets_result = await db.execute(select(func.count()).select_from(Target))
    total_assets = assets_result.scalar() or 0

    # Count vulnerabilities from stat records
    stats_result = await db.execute(
        select(StatRecord).where(StatRecord.result.contains("vulnerable"))
    )
    vuln_records = stats_result.scalars().all()
    total_vulns = len(vuln_records)

    return StatsOverviewResponse(
        total_tasks=total_tasks,
        total_assets=total_assets,
        total_vulns=total_vulns,
        by_severity={"critical": 0, "high": 0, "medium": 0, "low": 0},
    )


@router.get("/vulns")
async def get_vuln_stats(
    vuln_id: str = None,
    start_date: str = None,
    end_date: str = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get vulnerability statistics."""
    # TODO: Implement actual statistics calculation
    return {
        "vuln_id": vuln_id or "all",
        "total_executions": 0,
        "success_rate": 0.0,
        "vuln_found_rate": 0.0,
        "avg_duration": 0,
    }
