from datetime import date, datetime, timezone
from enum import StrEnum

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Status(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLIANT = "compliant"
    NOT_APPLICABLE = "not_applicable"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    company: Mapped["Company"] = relationship(back_populates="users")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    # Questionnaire answers, keyed by question id (see data/questionnaire.yaml)
    profile: Mapped[dict | None] = mapped_column(JSON, default=None)
    assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    users: Mapped[list[User]] = relationship(back_populates="company")
    regulations: Mapped[list["CompanyRegulation"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class Regulation(Base):
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
    applicability: Mapped[dict] = mapped_column(JSON, default=dict)

    requirements: Mapped[list["Requirement"]] = relationship(
        back_populates="regulation", cascade="all, delete-orphan", order_by="Requirement.position"
    )


class Requirement(Base):
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

    regulation: Mapped[Regulation] = relationship(back_populates="requirements")


class CompanyRegulation(Base):
    __tablename__ = "company_regulations"
    __table_args__ = (UniqueConstraint("company_id", "regulation_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    regulation_id: Mapped[int] = mapped_column(ForeignKey("regulations.id"))
    reasons: Mapped[list] = mapped_column(JSON, default=list)

    company: Mapped[Company] = relationship(back_populates="regulations")
    regulation: Mapped[Regulation] = relationship()


class RequirementStatus(Base):
    __tablename__ = "requirement_statuses"
    __table_args__ = (UniqueConstraint("company_id", "requirement_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id"))
    status: Mapped[str] = mapped_column(String(32), default=Status.NOT_STARTED)
    note: Mapped[str | None] = mapped_column(Text, default=None)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    requirement_id: Mapped[int | None] = mapped_column(ForeignKey("requirements.id"), default=None)
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str | None] = mapped_column(String(128), default=None)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    # Plain text extracted on upload; this is what the future RAG agent indexes.
    extracted_text: Mapped[str | None] = mapped_column(Text, default=None)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    requirement: Mapped[Requirement | None] = relationship()


class RegulatoryUpdate(Base):
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
