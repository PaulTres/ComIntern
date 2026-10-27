from sqlalchemy import JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from comintern.schemas.base import Base
from comintern.schemas.regulations import Regulation


class CompanyRegulation(Base):
    """A regulation that applies to a company, with the reasons why."""

    __tablename__ = "company_regulations"
    __table_args__ = (UniqueConstraint("company_id", "regulation_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    regulation_id: Mapped[int] = mapped_column(ForeignKey("regulations.id"))
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)

    regulation: Mapped[Regulation] = relationship(lazy="selectin")
