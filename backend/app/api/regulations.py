from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company, CompanyRegulation, Regulation, Requirement, RequirementStatus
from app.schemas import RegulationDetail, RequirementOut, StatusIn
from app.security import current_company
from app.services import compliance

router = APIRouter(tags=["regulations"])


def _requirement_out(req: Requirement, row: RequirementStatus | None, docs) -> RequirementOut:
    return RequirementOut(
        id=req.id, key=req.key, title=req.title, description=req.description, reference=req.reference,
        weight=req.weight, evidence_hint=req.evidence_hint,
        status=row.status if row else "not_started", note=row.note if row else None,
        updated_at=row.updated_at if row else None,
        documents=[d for d in docs if d.requirement_id == req.id],
    )


@router.get("/regulations/{code}", response_model=RegulationDetail)
def regulation_detail(code: str, company: Company = Depends(current_company), db: Session = Depends(get_db)):
    cr = next((cr for cr in compliance.applicable(db, company) if cr.regulation.code == code), None)
    if cr is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Regulation not found or not applicable to your company")
    reg = cr.regulation
    status_rows = compliance.statuses(db, company)
    evidence = compliance.evidence_counts(db, company)
    docs = compliance.documents(db, company, regulation_code=code)
    base = compliance.summary(cr, compliance.score_regulation(reg, status_rows, evidence))
    return RegulationDetail(
        **base.model_dump(),
        authority=reg.authority,
        source_url=reg.source_url,
        requirements=[_requirement_out(r, status_rows.get(r.id), docs) for r in reg.requirements],
        updates=compliance.updates(db, company, regulation_code=code),
    )


def applicable_requirement(db: Session, company: Company, requirement_id: int) -> Requirement:
    req = db.get(Requirement, requirement_id)
    if req is None or not db.scalar(
        select(CompanyRegulation.id).where(
            CompanyRegulation.company_id == company.id, CompanyRegulation.regulation_id == req.regulation_id
        )
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Requirement not found")
    return req


@router.put("/requirements/{requirement_id}/status", response_model=RequirementOut)
def set_status(
    requirement_id: int, body: StatusIn, company: Company = Depends(current_company), db: Session = Depends(get_db)
):
    req = applicable_requirement(db, company, requirement_id)
    row = db.scalar(
        select(RequirementStatus).where(
            RequirementStatus.company_id == company.id, RequirementStatus.requirement_id == req.id
        )
    )
    if row is None:
        row = RequirementStatus(company_id=company.id, requirement_id=req.id)
        db.add(row)
    row.status = body.status
    row.note = body.note
    db.commit()
    docs = compliance.documents(db, company, regulation_code=req.regulation.code)
    return _requirement_out(req, row, docs)


@router.get("/catalog", tags=["regulations"])
def catalog_overview(db: Session = Depends(get_db)):
    """All regulations in the catalog (public), e.g. for a landing page."""
    return [
        {"code": r.code, "short_name": r.short_name, "name": r.name, "jurisdiction": r.jurisdiction, "category": r.category}
        for r in db.scalars(select(Regulation).order_by(Regulation.jurisdiction, Regulation.short_name))
    ]
