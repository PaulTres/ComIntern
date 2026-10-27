"""Placeholder for the future RAG compliance assistant.

Planned design: chunk and embed Document.extracted_text plus the official texts in
data/regulation_texts/, store vectors (e.g. pgvector), retrieve the most relevant
chunks for the question and the company's requirement statuses, and let an LLM
(Claude API) answer with citations. The request/response shape is final.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company, Document
from app.schemas import AskIn, AskOut
from app.security import current_company

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/ask", response_model=AskOut)
def ask(body: AskIn, company: Company = Depends(current_company), db: Session = Depends(get_db)):
    indexed = db.scalar(
        select(func.count()).where(Document.company_id == company.id, Document.extracted_text.is_not(None))
    )
    return AskOut(
        available=False,
        answer=(
            "The compliance assistant is not available yet. "
            f"{indexed} of your uploaded documents are already prepared for it and will be "
            "used to answer questions like this one once it launches."
        ),
    )
