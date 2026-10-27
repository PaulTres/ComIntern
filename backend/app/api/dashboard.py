from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company, Status
from app.schemas import DashboardOut, OpenTask, UpdateOut
from app.security import current_company
from app.services import compliance, scoring

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(company: Company = Depends(current_company), db: Session = Depends(get_db)):
    status_rows = compliance.statuses(db, company)
    evidence = compliance.evidence_counts(db, company)
    summaries, scores, open_tasks, all_items = [], [], [], []
    for cr in compliance.applicable(db, company):
        reg = cr.regulation
        s = compliance.score_regulation(reg, status_rows, evidence)
        scores.append(s)
        summaries.append(compliance.summary(cr, s))
        for req in reg.requirements:
            st = status_rows[req.id].status if req.id in status_rows else Status.NOT_STARTED
            all_items.append(scoring.Item(req.weight, st, evidence.get(req.id, 0) > 0))
            if st in (Status.NOT_STARTED, Status.IN_PROGRESS):
                open_tasks.append(OpenTask(
                    requirement_id=req.id, title=req.title, status=st, weight=req.weight,
                    regulation_code=reg.code, regulation_short_name=reg.short_name,
                ))
    # Highest weight first, then not-started before in-progress.
    open_tasks.sort(key=lambda t: (-t.weight, t.status != Status.NOT_STARTED))
    overall = scoring.overall(scores)
    return DashboardOut(
        company_name=company.name,
        assessed=company.assessed_at is not None,
        overall_score=overall,
        level=scoring.level(overall),
        totals=compliance.score_out(scoring.score_items(all_items)),
        regulations=summaries,
        open_tasks=open_tasks[:8],
        recent_documents=compliance.documents(db, company, limit=5),
        updates=compliance.updates(db, company, relevant_only=True)[:5],
    )


@router.get("/updates", response_model=list[UpdateOut], tags=["updates"])
def list_updates(relevant_only: bool = False, company: Company = Depends(current_company), db: Session = Depends(get_db)):
    return compliance.updates(db, company, relevant_only=relevant_only)
