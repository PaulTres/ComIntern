from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from comintern.schemas.base import Base

if TYPE_CHECKING:
    from comintern.schemas.regulations import Regulation


class Requirement(Base):
    """One thing a regulation asks for, weighted 1 to 3 in the score."""

    __tablename__ = "requirements"
    __table_args__ = (UniqueConstraint("regulation_id", "key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    regulation_id: Mapped[int] = mapped_column(ForeignKey("regulations.id"))
    key: Mapped[str] = mapped_column(String(64))
    position: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    reference: Mapped[str | None] = mapped_column(String(128), default=None)
    weight: Mapped[int] = mapped_column(Integer, default=1)
    evidence_hint: Mapped[str | None] = mapped_column(Text, default=None)

    regulation: Mapped[Regulation] = relationship(
        back_populates="requirements", lazy="selectin"
    )
