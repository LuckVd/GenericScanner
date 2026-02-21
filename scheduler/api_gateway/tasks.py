"""Task API routes."""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.models.task import Task, TaskStatus
from common.utils.database import get_db
from scheduler.api_gateway.schemas import (
    TaskCreate,
    TaskDetailResponse,
    TaskListResponse,
    TaskPauseResponse,
    TaskResponse,
    TaskResultResponse,
    TaskResumeResponse,
)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Create a new scan task."""
    task = Task(
        name=task_data.name,
        targets=task_data.targets,
        auth=task_data.auth,
        policy=task_data.policy,
        vuln_ids=task_data.vuln_ids,
        priority=task_data.priority,
        options=task_data.options,
        status=TaskStatus.PENDING,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    return TaskResponse(
        id=task.id,
        name=task.name,
        status=task.status.value,
        progress={"total": task.progress_total, "completed": task.progress_completed},
        created_at=task.created_at,
    )


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: str | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """Get task list."""
    query = select(Task)

    if status:
        try:
            status_enum = TaskStatus(status)
            query = query.where(Task.status == status_enum)
        except ValueError:
            pass

    # Count total
    count_query = select(Task.id)
    if status:
        try:
            status_enum = TaskStatus(status)
            count_query = count_query.where(Task.status == status_enum)
        except ValueError:
            pass

    from sqlalchemy import func

    total_result = await db.execute(select(func.count()).select_from(Task))
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(Task.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return TaskListResponse(
        total=total,
        page=page,
        size=size,
        items=[
            TaskResponse(
                id=t.id,
                name=t.name,
                status=t.status.value,
                progress={"total": t.progress_total, "completed": t.progress_completed},
                created_at=t.created_at,
            )
            for t in tasks
        ],
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskDetailResponse:
    """Get task details."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskDetailResponse(
        id=task.id,
        name=task.name,
        targets=task.targets,
        auth=task.auth,
        policy=task.policy,
        vuln_ids=task.vuln_ids,
        priority=task.priority,
        options=task.options,
        status=task.status.value,
        progress={"total": task.progress_total, "completed": task.progress_completed},
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post("/{task_id}/pause", response_model=TaskPauseResponse)
async def pause_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskPauseResponse:
    """Pause a running task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.RUNNING:
        raise HTTPException(
            status_code=400, detail="Can only pause running tasks"
        )

    task.status = TaskStatus.PAUSED
    await db.flush()

    return TaskPauseResponse(
        id=task.id,
        status=task.status.value,
        message="Task paused successfully",
    )


@router.post("/{task_id}/resume", response_model=TaskResumeResponse)
async def resume_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskResumeResponse:
    """Resume a paused task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.PAUSED:
        raise HTTPException(
            status_code=400, detail="Can only resume paused tasks"
        )

    task.status = TaskStatus.RUNNING
    await db.flush()

    return TaskResumeResponse(
        id=task.id,
        status=task.status.value,
        message="Task resumed successfully",
    )


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)

    return {"message": "Task deleted successfully"}


@router.get("/{task_id}/results", response_model=TaskResultResponse)
async def get_task_results(
    task_id: str,
    severity: str | None = Query(None, description="Filter by severity"),
    db: AsyncSession = Depends(get_db),
) -> TaskResultResponse:
    """Get task scan results."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # TODO: Implement actual result fetching from stat_records
    return TaskResultResponse(
        task_id=task_id,
        total_vulns=0,
        by_severity={"critical": 0, "high": 0, "medium": 0, "low": 0},
        results=[],
    )
