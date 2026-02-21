"""Scan node model."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from common.models.base import Base, TimestampMixin


class ScanNode(Base, TimestampMixin):
    """Scan node model for distributed scanners."""

    __tablename__ = "scan_nodes"

    id: Mapped[str] = mapped_column(
        String(50), primary_key=True
    )  # Node identifier
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="offline")
    cpu_load: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_load: Mapped[float | None] = mapped_column(Float, nullable=True)
    tasks_running: Mapped[int] = mapped_column(Integer, default=0)
    max_tasks: Mapped[int] = mapped_column(Integer, default=100)
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<ScanNode {self.id}: {self.status}>"

    @property
    def tag_list(self) -> list[str]:
        """Get tags as list."""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @tag_list.setter
    def tag_list(self, value: list[str]) -> None:
        """Set tags from list."""
        self.tags = ",".join(value)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "status": self.status,
            "load": {
                "cpu": self.cpu_load,
                "memory": self.memory_load,
            },
            "tasks_running": self.tasks_running,
            "max_tasks": self.max_tasks,
            "last_heartbeat": (
                self.last_heartbeat.isoformat() if self.last_heartbeat else None
            ),
        }
