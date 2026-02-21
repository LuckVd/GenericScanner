"""Task Manager - Manages scan task lifecycle."""

import asyncio
import ipaddress
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.constants import DEFAULT_CONCURRENCY, DEFAULT_PRIORITY, DEFAULT_TIMEOUT
from common.models.task import Task, TaskStatus
from common.utils.database import get_db_context

logger = logging.getLogger(__name__)


class TaskManager:
    """Manages scan tasks lifecycle."""

    def __init__(self) -> None:
        self._running_tasks: dict[str, asyncio.Task] = {}

    async def create_task(
        self,
        name: str,
        targets: list[str],
        auth: dict | None = None,
        policy: str = "full",
        vuln_ids: list[str] | None = None,
        priority: int = DEFAULT_PRIORITY,
        options: dict | None = None,
    ) -> Task:
        """Create a new scan task."""
        async with get_db_context() as db:
            task = Task(
                name=name,
                targets=targets,
                auth=auth,
                policy=policy,
                vuln_ids=vuln_ids,
                priority=priority,
                options=options or {},
                status=TaskStatus.PENDING,
            )

            # Calculate total targets (expand CIDR if needed)
            total_targets = self._count_targets(targets)
            task.progress_total = total_targets

            db.add(task)
            await db.flush()
            await db.refresh(task)

            logger.info(f"Created task {task.id}: {name}")
            return task

    async def get_task(self, task_id: str) -> Task | None:
        """Get task by ID."""
        async with get_db_context() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            return result.scalar_one_or_none()

    async def list_tasks(
        self,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Task], int]:
        """List tasks with pagination."""
        async with get_db_context() as db:
            query = select(Task)
            count_query = select(Task.id)

            if status:
                try:
                    status_enum = TaskStatus(status)
                    query = query.where(Task.status == status_enum)
                    count_query = count_query.where(Task.status == status_enum)
                except ValueError:
                    pass

            # Get total count
            from sqlalchemy import func

            total_result = await db.execute(
                select(func.count()).select_from(Task)
            )
            total = total_result.scalar() or 0

            # Get paginated results
            query = query.order_by(Task.created_at.desc())
            query = query.offset((page - 1) * size).limit(size)

            result = await db.execute(query)
            tasks = result.scalars().all()

            return list(tasks), total

    async def pause_task(self, task_id: str) -> bool:
        """Pause a running task."""
        async with get_db_context() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if not task or task.status != TaskStatus.RUNNING:
                return False

            task.status = TaskStatus.PAUSED
            await db.flush()

            logger.info(f"Paused task {task_id}")
            return True

    async def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        async with get_db_context() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if not task or task.status != TaskStatus.PAUSED:
                return False

            task.status = TaskStatus.RUNNING
            await db.flush()

            logger.info(f"Resumed task {task_id}")
            return True

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        async with get_db_context() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                return False

            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                return False

            task.status = TaskStatus.FAILED
            task.error_message = "Task cancelled by user"
            await db.flush()

            logger.info(f"Cancelled task {task_id}")
            return True

    async def update_progress(
        self, task_id: str, completed: int, total: int | None = None
    ) -> None:
        """Update task progress."""
        async with get_db_context() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if task:
                task.progress_completed = completed
                if total is not None:
                    task.progress_total = total
                await db.flush()

    async def mark_running(self, task_id: str) -> None:
        """Mark task as running."""
        async with get_db_context() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if task:
                task.status = TaskStatus.RUNNING
                await db.flush()

    async def mark_completed(self, task_id: str) -> None:
        """Mark task as completed."""
        async with get_db_context() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if task:
                task.status = TaskStatus.COMPLETED
                task.progress_completed = task.progress_total
                await db.flush()

                logger.info(f"Task {task_id} completed")

    async def mark_failed(self, task_id: str, error: str) -> None:
        """Mark task as failed."""
        async with get_db_context() as db:
            result = await db.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if task:
                task.status = TaskStatus.FAILED
                task.error_message = error
                await db.flush()

                logger.error(f"Task {task_id} failed: {error}")

    def _count_targets(self, targets: list[str]) -> int:
        """Count total targets, expanding CIDR ranges."""
        count = 0
        for target in targets:
            try:
                # Check if it's a CIDR range
                if "/" in target:
                    network = ipaddress.ip_network(target, strict=False)
                    count += network.num_addresses
                else:
                    count += 1
            except ValueError:
                count += 1  # Domain name or invalid IP
        return count

    def split_targets(
        self, targets: list[str], chunk_size: int = 256
    ) -> list[list[str]]:
        """Split targets into chunks for parallel scanning."""
        all_targets = []

        for target in targets:
            try:
                if "/" in target:
                    network = ipaddress.ip_network(target, strict=False)
                    for ip in network.hosts():
                        all_targets.append(str(ip))
                else:
                    all_targets.append(target)
            except ValueError:
                all_targets.append(target)

        # Split into chunks
        chunks = []
        for i in range(0, len(all_targets), chunk_size):
            chunks.append(all_targets[i : i + chunk_size])

        return chunks


# Global task manager instance
task_manager = TaskManager()
