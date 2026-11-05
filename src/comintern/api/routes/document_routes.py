from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse

from comintern.api.dependencies import CurrentUserDependency, DocumentServiceDependency
from comintern.models.compliance import DocumentResponseModel

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentResponseModel])
async def list_documents(
    user: CurrentUserDependency,
    document_service: DocumentServiceDependency,
    regulation: str | None = None,
) -> list[DocumentResponseModel]:
    return await document_service.list_documents(user.company_id, regulation)


@router.post("", response_model=DocumentResponseModel, status_code=HTTPStatus.CREATED)
async def upload_document(
    file: Annotated[UploadFile, File()],
    user: CurrentUserDependency,
    document_service: DocumentServiceDependency,
    requirement_id: Annotated[int | None, Form()] = None,
) -> DocumentResponseModel:
    """Store an evidence file, optionally linked to a requirement, and index its text for the assistant."""
    return await document_service.upload(user.company_id, file, requirement_id)


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    user: CurrentUserDependency,
    document_service: DocumentServiceDependency,
) -> FileResponse:
    path, filename, mime_type = await document_service.get_file(
        user.company_id, document_id
    )
    return FileResponse(path, media_type=mime_type, filename=filename)


@router.delete("/{document_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_document(
    document_id: int,
    user: CurrentUserDependency,
    document_service: DocumentServiceDependency,
) -> None:
    await document_service.delete(user.company_id, document_id)
