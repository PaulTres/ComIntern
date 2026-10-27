from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Status


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    company_name: str = Field(min_length=1, max_length=255)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class CompanyOut(ORM):
    id: int
    name: str
    profile: dict[str, Any] | None
    assessed_at: datetime | None


class UserOut(ORM):
    id: int
    email: str
    company: CompanyOut


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CompanyUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    profile: dict[str, Any] | None = None


class ScoreOut(BaseModel):
    score: int | None
    level: str
    total: int
    compliant: int
    in_progress: int
    not_started: int
    not_applicable: int
    evidenced: int


class RegulationSummary(BaseModel):
    code: str
    name: str
    short_name: str
    jurisdiction: str
    category: str
    summary: str
    reasons: list[str]
    score: ScoreOut


class DocumentOut(BaseModel):
    id: int
    filename: str
    mime_type: str | None
    size_bytes: int
    uploaded_at: datetime
    has_text: bool
    requirement_id: int | None
    requirement_title: str | None
    regulation_code: str | None
    regulation_short_name: str | None


class RequirementOut(BaseModel):
    id: int
    key: str
    title: str
    description: str
    reference: str | None
    weight: int
    evidence_hint: str | None
    status: Status
    note: str | None
    updated_at: datetime | None
    documents: list[DocumentOut]


class UpdateOut(ORM):
    id: int
    regulation_code: str
    title: str
    summary: str
    published_on: date
    effective_on: date | None
    kind: str
    severity: str
    source_url: str | None
    relevant: bool = False


class RegulationDetail(RegulationSummary):
    authority: str | None
    source_url: str | None
    requirements: list[RequirementOut]
    updates: list[UpdateOut]


class StatusIn(BaseModel):
    status: Status
    note: str | None = Field(default=None, max_length=5000)


class OpenTask(BaseModel):
    requirement_id: int
    title: str
    status: Status
    weight: int
    regulation_code: str
    regulation_short_name: str


class DashboardOut(BaseModel):
    company_name: str
    assessed: bool
    overall_score: int | None
    level: str
    totals: ScoreOut
    regulations: list[RegulationSummary]
    open_tasks: list[OpenTask]
    recent_documents: list[DocumentOut]
    updates: list[UpdateOut]


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    regulation_code: str | None = None


class AskOut(BaseModel):
    available: bool
    answer: str
    sources: list[dict[str, Any]] = []
