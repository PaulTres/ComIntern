from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from comintern.schemas.base import Base
from comintern.schemas.requirements import Requirement


class Regulation(Base):
    """A regulation from the YAML catalog, with its applicability rules."""

    __tablename__ = "regulations"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    short_name: Mapped[str] = mapped_column(String(64))
    jurisdiction: Mapped[str] = mapped_column(String(8))  # EU / DE / RO
    category: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text)
    authority: Mapped[str | None] = mapped_column(String(255), default=None)
    source_url: Mapped[str | None] = mapped_column(String(512), default=None)
    applicability: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    requirements: Mapped[list[Requirement]] = relationship(
        back_populates="regulation",
        cascade="all, delete-orphan",
        order_by=Requirement.position,
        lazy="selectin",
    )
