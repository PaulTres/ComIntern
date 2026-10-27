import mimetypes
import re
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Company, Document
from app.schemas import DocumentOut
from app.security import current_company
from app.services import compliance
from app.services.text_extraction import extract_text
from app.api.regulations import applicable_requirement

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_SUFFIXES = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".txt", ".md", ".csv", ".png", ".jpg", ".jpeg"}


def _owned(db: Session, company: Company, document_id: int) -> Document:
    doc = db.get(Document, document_id)
    if doc is None or doc.company_id != company.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(regulation: str | None = None, company: Company = Depends(current_company), db: Session = Depends(get_db)):
    return compliance.documents(db, company, regulation_code=regulation)


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    requirement_id: int | None = Form(None),
    company: Company = Depends(current_company),
    db: Session = Depends(get_db),
):
    if requirement_id is not None:
        applicable_requirement(db, company, requirement_id)
    filename = re.sub(r"[^\w.\- ]", "_", file.filename or "upload").strip() or "upload"
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"File type {suffix or '(none)'} is not supported")

    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, f"Files are limited to {settings.max_upload_mb} MB")

    company_dir = settings.upload_dir / str(company.id)
    company_dir.mkdir(parents=True, exist_ok=True)
    path = company_dir / f"{uuid.uuid4().hex}{suffix}"
    path.write_bytes(content)
    mime = file.content_type or mimetypes.guess_type(filename)[0]

    doc = Document(
        company_id=company.id, requirement_id=requirement_id, filename=filename,
        stored_path=str(path.relative_to(settings.upload_dir)), mime_type=mime, size_bytes=len(content),
        extracted_text=extract_text(path, mime),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return compliance.document_out(doc)


@router.get("/{document_id}/download")
def download_document(document_id: int, company: Company = Depends(current_company), db: Session = Depends(get_db)):
    doc = _owned(db, company, document_id)
    return FileResponse(settings.upload_dir / doc.stored_path, media_type=doc.mime_type, filename=doc.filename)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, company: Company = Depends(current_company), db: Session = Depends(get_db)):
    doc = _owned(db, company, document_id)
    (settings.upload_dir / doc.stored_path).unlink(missing_ok=True)
    db.delete(doc)
    db.commit()
