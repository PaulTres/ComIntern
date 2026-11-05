"""Regulations, requirements, scores, evidence, updates and the dashboard, as the API returns them."""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ComplianceStatus(StrEnum):
    """Where a company stands on one requirement."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLIANT = "compliant"
    NOT_APPLICABLE = "not_applicable"


class ScoreResponseModel(BaseModel):
    score: int | None
    level: str
    total: int
    compliant: int
    in_progress: int
    not_started: int
    not_applicable: int
    evidenced: int


class RegulationSummaryResponseModel(BaseModel):
    code: str
    name: str
    short_name: str
    jurisdiction: str
    category: str
    summary: str
    reasons: list[str]
    score: ScoreResponseModel


class DocumentResponseModel(BaseModel):
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


class RequirementResponseModel(BaseModel):
    id: int
    key: str
    title: str
    description: str
    reference: str | None
    weight: int
    evidence_hint: str | None
    status: ComplianceStatus
    note: str | None
    updated_at: datetime | None
    documents: list[DocumentResponseModel]


class UpdateResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class RegulationDetailResponseModel(RegulationSummaryResponseModel):
    authority: str | None
    source_url: str | None
    requirements: list[RequirementResponseModel]
    updates: list[UpdateResponseModel]


class StatusUpdateRequestModel(BaseModel):
    status: ComplianceStatus
    note: str | None = Field(default=None, max_length=5000)


class OpenTaskResponseModel(BaseModel):
    requirement_id: int
    title: str
    status: ComplianceStatus
    weight: int
    regulation_code: str
    regulation_short_name: str


class DashboardResponseModel(BaseModel):
    company_name: str
    assessed: bool
    overall_score: int | None
    level: str
    totals: ScoreResponseModel
    regulations: list[RegulationSummaryResponseModel]
    open_tasks: list[OpenTaskResponseModel]
    recent_documents: list[DocumentResponseModel]
    updates: list[UpdateResponseModel]


class CatalogEntryResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    short_name: str
    name: str
    jurisdiction: str
    category: str
