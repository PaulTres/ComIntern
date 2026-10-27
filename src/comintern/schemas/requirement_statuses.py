from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from comintern.models.compliance import ComplianceStatus
from comintern.schemas.base import Base, enum_column, utcnow


class RequirementStatus(Base):
    """A company's status and note on one requirement; no row means not started."""

    __tablename__ = "requirement_statuses"
    __table_args__ = (UniqueConstraint("company_id", "requirement_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id"))
    status: Mapped[ComplianceStatus] = mapped_column(
        enum_column(ComplianceStatus, "compliance_status"),
        default=ComplianceStatus.NOT_STARTED,
    )
    note: Mapped[str | None] = mapped_column(Text, default=None)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
