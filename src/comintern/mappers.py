"""Turn ORM rows into the response models the API returns."""

from comintern.models.compliance import (
    ComplianceStatus,
    DocumentResponseModel,
    RegulationSummaryResponseModel,
    RequirementResponseModel,
    ScoreResponseModel,
)
from comintern.rules import scoring
from comintern.schemas import (
    CompanyRegulation,
    Document,
    Regulation,
    Requirement,
    RequirementStatus,
)


def get_status(
    statuses: dict[int, RequirementStatus], requirement_id: int
) -> ComplianceStatus:
    """
    :return: The company's status on the requirement; not started when it never set one.
    """
    row = statuses.get(requirement_id)
    return row.status if row else ComplianceStatus.NOT_STARTED


def score_regulation(
    regulation: Regulation,
    statuses: dict[int, RequirementStatus],
    evidence_counts: dict[int, int],
) -> scoring.Score:
    return scoring.score_items(
        [
            scoring.Item(
                requirement.weight,
                get_status(statuses, requirement.id),
                evidence_counts.get(requirement.id, 0) > 0,
            )
            for requirement in regulation.requirements
        ]
    )


def to_score_response(score: scoring.Score) -> ScoreResponseModel:
    return ScoreResponseModel(
        score=score.score,
        level=score.level,
        total=score.total,
        compliant=score.compliant,
        in_progress=score.in_progress,
        not_started=score.not_started,
        not_applicable=score.not_applicable,
        evidenced=score.evidenced,
    )


def to_regulation_summary(
    company_regulation: CompanyRegulation, score: scoring.Score
) -> RegulationSummaryResponseModel:
    regulation = company_regulation.regulation
    return RegulationSummaryResponseModel(
        code=regulation.code,
        name=regulation.name,
        short_name=regulation.short_name,
        jurisdiction=regulation.jurisdiction,
        category=regulation.category,
        summary=regulation.summary,
        reasons=company_regulation.reasons,
        score=to_score_response(score),
    )


def to_document_response(document: Document) -> DocumentResponseModel:
    requirement = document.requirement
    return DocumentResponseModel(
        id=document.id,
        filename=document.filename,
        mime_type=document.mime_type,
        size_bytes=document.size_bytes,
        uploaded_at=document.uploaded_at,
        has_text=bool(document.extracted_text),
        requirement_id=document.requirement_id,
        requirement_title=requirement.title if requirement else None,
        regulation_code=requirement.regulation.code if requirement else None,
        regulation_short_name=requirement.regulation.short_name
        if requirement
        else None,
    )


def to_requirement_response(
    requirement: Requirement,
    status: RequirementStatus | None,
    documents: list[DocumentResponseModel],
) -> RequirementResponseModel:
    return RequirementResponseModel(
        id=requirement.id,
        key=requirement.key,
        title=requirement.title,
        description=requirement.description,
        reference=requirement.reference,
        weight=requirement.weight,
        evidence_hint=requirement.evidence_hint,
        status=status.status if status else ComplianceStatus.NOT_STARTED,
        note=status.note if status else None,
        updated_at=status.updated_at if status else None,
        documents=[
            document
            for document in documents
            if document.requirement_id == requirement.id
        ],
    )
