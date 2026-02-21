"""Vulnerability case model."""

from typing import Any

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.models.base import Base, TimestampMixin


class VulnCase(Base, TimestampMixin):
    """Vulnerability case model for POC plugins."""

    __tablename__ = "vuln_cases"

    id: Mapped[str] = mapped_column(
        String(100), primary_key=True
    )  # CVE ID or custom ID
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    md5: Mapped[str | None] = mapped_column(String(32), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<VulnCase {self.id}: {self.name}>"

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
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "tags": self.tag_list,
            "fingerprint": self.fingerprint,
            "file_path": self.file_path,
            "md5": self.md5,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
