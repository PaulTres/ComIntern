"""Company-level compliance state: applicable regulations, requirement statuses, scores."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app import schemas
from app.models import (
    Company,
    CompanyRegulation,
    Document,
    Regulation,
    RegulatoryUpdate,
    Requirement,
    RequirementStatus,
    Status,
)
from app.services import applicability, scoring


def reassess(db: Session, company: Company) -> None:
    """Re-run the applicability engine for the company's current profile."""
    profile = company.profile or {}
    current = {cr.regulation_id: cr for cr in company.regulations}
    keep = set()
    for reg in db.scalars(select(Regulation)):
        reasons = applicability.assess(reg.applicability, profile)
        if not reasons:
            continue
        keep.add(reg.id)
        if reg.id in current:
            current[reg.id].reasons = reasons
        else:
            company.regulations.append(CompanyRegulation(regulation_id=reg.id, reasons=reasons))
    for reg_id, cr in current.items():
        if reg_id not in keep:
            company.regulations.remove(cr)
    company.assessed_at = datetime.now(timezone.utc)
    db.commit()


def applicable(db: Session, company: Company) -> list[CompanyRegulation]:
    stmt = (
        select(CompanyRegulation)
        .where(CompanyRegulation.company_id == company.id)
        .join(Regulation)
        .options(selectinload(CompanyRegulation.regulation).selectinload(Regulation.requirements))
        .order_by(Regulation.jurisdiction, Regulation.short_name)
    )
    return list(db.scalars(stmt))


def statuses(db: Session, company: Company) -> dict[int, RequirementStatus]:
    rows = db.scalars(select(RequirementStatus).where(RequirementStatus.company_id == company.id))
    return {r.requirement_id: r for r in rows}


def evidence_counts(db: Session, company: Company) -> dict[int, int]:
    stmt = (
        select(Document.requirement_id, func.count())
        .where(Document.company_id == company.id, Document.requirement_id.is_not(None))
        .group_by(Document.requirement_id)
    )
    return dict(db.execute(stmt).all())


def _status(status_rows: dict[int, RequirementStatus], req_id: int) -> str:
    row = status_rows.get(req_id)
    return row.status if row else Status.NOT_STARTED


def score_regulation(reg: Regulation, status_rows, evidence) -> scoring.Score:
    return scoring.score_items(
        [scoring.Item(r.weight, _status(status_rows, r.id), evidence.get(r.id, 0) > 0) for r in reg.requirements]
    )


def score_out(s: scoring.Score) -> schemas.ScoreOut:
    return schemas.ScoreOut(
        score=s.score, level=s.level, total=s.total, compliant=s.compliant, in_progress=s.in_progress,
        not_started=s.not_started, not_applicable=s.not_applicable, evidenced=s.evidenced,
    )


def summary(cr: CompanyRegulation, s: scoring.Score) -> schemas.RegulationSummary:
    reg = cr.regulation
    return schemas.RegulationSummary(
        code=reg.code, name=reg.name, short_name=reg.short_name, jurisdiction=reg.jurisdiction,
        category=reg.category, summary=reg.summary, reasons=cr.reasons, score=score_out(s),
    )


def document_out(doc: Document) -> schemas.DocumentOut:
    req = doc.requirement
    return schemas.DocumentOut(
        id=doc.id, filename=doc.filename, mime_type=doc.mime_type, size_bytes=doc.size_bytes,
        uploaded_at=doc.uploaded_at, has_text=bool(doc.extracted_text),
        requirement_id=doc.requirement_id,
        requirement_title=req.title if req else None,
        regulation_code=req.regulation.code if req else None,
        regulation_short_name=req.regulation.short_name if req else None,
    )


def documents(db: Session, company: Company, regulation_code: str | None = None, limit: int | None = None):
    stmt = (
        select(Document)
        .where(Document.company_id == company.id)
        .options(selectinload(Document.requirement).selectinload(Requirement.regulation))
        .order_by(Document.uploaded_at.desc())
    )
    if regulation_code:
        stmt = stmt.join(Requirement).join(Regulation).where(Regulation.code == regulation_code)
    if limit:
        stmt = stmt.limit(limit)
    return [document_out(d) for d in db.scalars(stmt)]


def updates(db: Session, company: Company, relevant_only: bool = False, regulation_code: str | None = None):
    codes = {cr.regulation.code for cr in company.regulations}
    stmt = select(RegulatoryUpdate).order_by(RegulatoryUpdate.published_on.desc())
    if regulation_code:
        stmt = stmt.where(RegulatoryUpdate.regulation_code == regulation_code)
    result = []
    for upd in db.scalars(stmt):
        out = schemas.UpdateOut.model_validate(upd)
        out.relevant = upd.regulation_code in codes
        if out.relevant or not relevant_only:
            result.append(out)
    return result
