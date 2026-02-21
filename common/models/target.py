"""Target model for scan targets."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models.base import Base, TimestampMixin


class Service(Base):
    """Service model for target services."""

    __tablename__ = "services"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    target_id: Mapped[str] = mapped_column(String(36), ForeignKey("targets.id"))
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    banner: Mapped[str | None] = mapped_column(Text, nullable=True)
    ssl: Mapped[bool] = mapped_column(default=False)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "port": self.port,
            "name": self.name,
            "banner": self.banner,
            "ssl": self.ssl,
        }


class Fingerprint(Base):
    """Fingerprint model for target fingerprints."""

    __tablename__ = "fingerprints"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    target_id: Mapped[str] = mapped_column(String(36), ForeignKey("targets.id"))
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "name": self.name,
            "version": self.version,
            "tags": self.tags.split(",") if self.tags else [],
        }


class Target(Base, TimestampMixin):
    """Target model for scan targets."""

    __tablename__ = "targets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ports: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)
    discovered_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    last_scan: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    services_rel: Mapped[list["Service"]] = relationship(
        "Service", backref="target", cascade="all, delete-orphan"
    )
    fingerprints_rel: Mapped[list["Fingerprint"]] = relationship(
        "Fingerprint", backref="target", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Target {self.id}: {self.ip or self.domain}>"

    @property
    def port_list(self) -> list[int]:
        """Get ports as list."""
        if not self.ports:
            return []
        return [int(p) for p in self.ports.split(",") if p.strip()]

    @port_list.setter
    def port_list(self, value: list[int]) -> None:
        """Set ports from list."""
        self.ports = ",".join(str(p) for p in value)

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
            "ip": self.ip,
            "domain": self.domain,
            "ports": self.port_list,
            "services": [s.to_dict() for s in self.services_rel],
            "fingerprints": [f.to_dict() for f in self.fingerprints_rel],
            "tags": self.tag_list,
            "discovered_by": self.discovered_by,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
        }
