from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from comintern.schemas.base import Base, utcnow
from comintern.schemas.requirements import Requirement


class Document(Base):
    """An uploaded evidence file, optionally linked to the requirement it proves."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    requirement_id: Mapped[int | None] = mapped_column(
        ForeignKey("requirements.id"), default=None
    )
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str | None] = mapped_column(String(128), default=None)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    # Plain text extracted on upload; it is what the assistant searches.
    extracted_text: Mapped[str | None] = mapped_column(Text, default=None)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )

    requirement: Mapped[Requirement | None] = relationship(lazy="selectin")
