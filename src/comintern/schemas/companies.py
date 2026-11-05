from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from comintern.schemas.base import Base
from comintern.schemas.company_regulations import CompanyRegulation

if TYPE_CHECKING:
    from comintern.schemas.users import User


class Company(Base):
    """A company and its questionnaire answers."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    # Questionnaire answers, keyed by question id (see catalog/questionnaire.yaml).
    profile: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    assessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    users: Mapped[list[User]] = relationship(back_populates="company", lazy="raise")
    # Loaded explicitly where needed, so signing in does not load every applicable regulation.
    regulations: Mapped[list[CompanyRegulation]] = relationship(
        cascade="all, delete-orphan", lazy="raise"
    )
