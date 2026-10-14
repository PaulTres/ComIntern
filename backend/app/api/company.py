from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import catalog
from app.database import get_db
from app.models import Company
from app.schemas import CompanyOut, CompanyUpdateIn, RegulationSummary
from app.security import current_company
from app.services import applicability, compliance

router = APIRouter(tags=["company"])


@router.get("/questionnaire")
def get_questionnaire():
    return catalog.questionnaire()


def validate_profile(answers: dict[str, Any]) -> dict[str, Any]:
    """Keep only known, visible answers and check required fields and types."""
    clean: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for step in catalog.questionnaire()["steps"]:
        for q in step["questions"]:
            qid = q["id"]
            if not applicability.visible(q, answers):
                continue
            value = answers.get(qid)
            if value is None or value == [] or value == "":
                if q.get("required"):
                    errors[qid] = "This question is required"
                continue
            options = {o["value"] for o in q.get("options", [])}
            match q["type"]:
                case "boolean" if isinstance(value, bool):
                    pass
                case "number" if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= q.get("min", 0):
                    pass
                case "single_select" if value in options:
                    pass
                case "multi_select" if isinstance(value, list) and value and set(value) <= options:
                    pass
                case _:
                    errors[qid] = "Invalid answer"
                    continue
            clean[qid] = value
    if errors:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, {"errors": errors})
    return clean


@router.get("/company", response_model=CompanyOut)
def get_company(company: Company = Depends(current_company)):
    return company


@router.put("/company", response_model=CompanyOut)
def update_company(body: CompanyUpdateIn, company: Company = Depends(current_company), db: Session = Depends(get_db)):
    if body.name is not None:
        company.name = body.name
    if body.profile is not None:
        company.profile = validate_profile(body.profile)
        compliance.reassess(db, company)
    db.commit()
    return company


@router.get("/company/regulations", response_model=list[RegulationSummary])
def applicable_regulations(company: Company = Depends(current_company), db: Session = Depends(get_db)):
    status_rows = compliance.statuses(db, company)
    evidence = compliance.evidence_counts(db, company)
    return [
        compliance.summary(cr, compliance.score_regulation(cr.regulation, status_rows, evidence))
        for cr in compliance.applicable(db, company)
    ]
