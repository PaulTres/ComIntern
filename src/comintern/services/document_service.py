import asyncio
import mimetypes
import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from comintern.configuration.config import DocumentsSettings
from comintern.database.session_factory import SessionFactory
from comintern.exceptions import AppError, AppErrorCode
from comintern.helpers.file_signature import content_matches_extension
from comintern.helpers.text_extraction import extract_text
from comintern.mappers import to_document_response
from comintern.models.compliance import DocumentResponseModel
from comintern.models.knowledge import PassageKind
from comintern.repositories.document_repository import DocumentRepository
from comintern.repositories.regulation_repository import RegulationRepository
from comintern.schemas import Document
from comintern.services.knowledge_base import KnowledgeBase

UNSAFE_FILENAME_CHARACTERS = re.compile(r"[^\w.\- ]")
DEFAULT_FILENAME = "upload"


def evidence_source_id(document_id: int) -> str:
    """:return: The knowledge-base source id of an evidence document."""
    return f"evidence:{document_id}"


class DocumentService:
    """Evidence uploads: the file on disk, its row, and its passages in the knowledge base."""

    def __init__(
        self,
        session_factory: SessionFactory,
        documents_settings: DocumentsSettings,
        knowledge_base: KnowledgeBase,
    ) -> None:
        self._session_factory = session_factory
        self._settings = documents_settings
        self._knowledge_base = knowledge_base

    async def list_documents(
        self, company_id: int, regulation_code: str | None
    ) -> list[DocumentResponseModel]:
        async with self._session_factory.get_session() as session:
            documents = await DocumentRepository(session).list_for_company(
                company_id, regulation_code
            )
            return [to_document_response(document) for document in documents]

    async def upload(
        self, company_id: int, file: UploadFile, requirement_id: int | None
    ) -> DocumentResponseModel:
        """
        Store the file, extract its text and index it, so the assistant can cite it.

        :raises AppError: REQUIREMENT_NOT_FOUND, UNSUPPORTED_FILE_TYPE, FILE_TOO_LARGE, VECTOR_STORE_UNAVAILABLE.
        """
        filename = (
            UNSAFE_FILENAME_CHARACTERS.sub(
                "_", file.filename or DEFAULT_FILENAME
            ).strip()
            or DEFAULT_FILENAME
        )
        suffix = Path(filename).suffix.lower()
        if suffix not in self._settings.allowed_extensions:
            raise AppError(
                AppErrorCode.UNSUPPORTED_FILE_TYPE,
                details=f"File type {suffix or '(none)'} is not supported",
            )
        content = await file.read(self._settings.max_file_size_bytes + 1)
        if len(content) > self._settings.max_file_size_bytes:
            max_megabytes = self._settings.max_file_size_bytes // (1024 * 1024)
            raise AppError(
                AppErrorCode.FILE_TOO_LARGE,
                details=f"Files are limited to {max_megabytes} MB",
            )
        if not content_matches_extension(suffix, content):
            raise AppError(
                AppErrorCode.UNSUPPORTED_FILE_TYPE,
                details=f"The file's content does not match its {suffix} extension",
            )

        async with self._session_factory.get_session() as session:
            requirement = None
            if requirement_id is not None:
                requirement = await RegulationRepository(
                    session
                ).get_applicable_requirement(company_id, requirement_id)
                if requirement is None:
                    raise AppError(AppErrorCode.REQUIREMENT_NOT_FOUND)

            stored_path = Path(str(company_id)) / f"{uuid.uuid4().hex}{suffix}"
            absolute_path = self._settings.upload_directory / stored_path
            absolute_path.parent.mkdir(parents=True, exist_ok=True)
            absolute_path.write_bytes(content)
            mime_type = file.content_type or mimetypes.guess_type(filename)[0]
            document = Document(
                company_id=company_id,
                requirement_id=requirement_id,
                filename=filename,
                stored_path=str(stored_path),
                mime_type=mime_type,
                size_bytes=len(content),
                extracted_text=await asyncio.to_thread(
                    extract_text, absolute_path, mime_type
                ),
                requirement=requirement,
            )
            try:
                await DocumentRepository(session).add(document)
                if document.extracted_text:
                    await self._knowledge_base.index(
                        evidence_source_id(document.id),
                        filename,
                        document.extracted_text,
                        kind=PassageKind.EVIDENCE,
                        company_id=company_id,
                        regulation_code=requirement.regulation.code
                        if requirement
                        else None,
                    )
            except BaseException:
                absolute_path.unlink(missing_ok=True)
                raise
            return to_document_response(document)

    async def get_file(
        self, company_id: int, document_id: int
    ) -> tuple[Path, str, str | None]:
        """
        :return: The file's path on disk, its original name and its media type.
        :raises AppError: DOCUMENT_NOT_FOUND when it does not exist or belongs to another company.
        """
        async with self._session_factory.get_session() as session:
            document = await DocumentRepository(session).get_owned(
                company_id, document_id
            )
            if document is None:
                raise AppError(AppErrorCode.DOCUMENT_NOT_FOUND)
            return (
                self._settings.upload_directory / document.stored_path,
                document.filename,
                document.mime_type,
            )

    async def delete(self, company_id: int, document_id: int) -> None:
        """
        Remove the passages, the row and the file, in that order.

        :raises AppError: DOCUMENT_NOT_FOUND when it does not exist or belongs to another company.
        """
        async with self._session_factory.get_session() as session:
            documents = DocumentRepository(session)
            document = await documents.get_owned(company_id, document_id)
            if document is None:
                raise AppError(AppErrorCode.DOCUMENT_NOT_FOUND)
            await self._knowledge_base.remove(evidence_source_id(document.id))
            await documents.delete(document)
            stored_path = document.stored_path
        (self._settings.upload_directory / stored_path).unlink(missing_ok=True)
