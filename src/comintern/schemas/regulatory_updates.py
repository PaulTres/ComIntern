from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from comintern.schemas.base import Base


class RegulatoryUpdate(Base):
    """A deadline, amendment or guidance item from the curated updates feed."""

    __tablename__ = "regulatory_updates"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    regulation_code: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    published_on: Mapped[date] = mapped_column(Date)
    effective_on: Mapped[date | None] = mapped_column(Date, default=None)
    kind: Mapped[str] = mapped_column(String(32))  # deadline / amendment / guidance
    severity: Mapped[str] = mapped_column(String(16))  # info / important / critical
    source_url: Mapped[str | None] = mapped_column(String(512), default=None)
