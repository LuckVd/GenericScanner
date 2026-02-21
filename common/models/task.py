"""Task model for scan jobs."""

import enum
import uuid
from typing import Any

from sqlalchemy import JSON, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.models.base import Base, TimestampMixin


class TaskStatus(str, enum.Enum):
    """Task status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(Base, TimestampMixin):
    """Scan task model."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    targets: Mapped[list] = mapped_column(JSON, nullable=False)
    auth: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    policy: Mapped[str] = mapped_column(String(50), nullable=False, default="full")
    vuln_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING
    )
    progress_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Task {self.id}: {self.name}>"

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.progress_total == 0:
            return 0.0
        return (self.progress_completed / self.progress_total) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "targets": self.targets,
            "auth": self.auth,
            "policy": self.policy,
            "vuln_ids": self.vuln_ids,
            "priority": self.priority,
            "options": self.options,
            "status": self.status.value,
            "progress": {
                "total": self.progress_total,
                "completed": self.progress_completed,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
