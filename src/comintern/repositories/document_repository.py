from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from comintern.schemas import Document, Regulation, Requirement


class DocumentRepository:
    """A company's evidence documents."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_company(
        self,
        company_id: int,
        regulation_code: str | None = None,
        limit: int | None = None,
    ) -> list[Document]:
        """
        :param company_id: The company.
        :param regulation_code: Only the documents linked to this regulation's requirements.
        :param limit: At most this many, newest first.
        :return: The documents, newest first.
        """
        statement = (
            select(Document)
            .where(Document.company_id == company_id)
            .order_by(Document.uploaded_at.desc())
        )
        if regulation_code:
            statement = (
                statement.join(Requirement)
                .join(Regulation)
                .where(Regulation.code == regulation_code)
            )
        if limit:
            statement = statement.limit(limit)
        return list(await self._session.scalars(statement))

    async def get_owned(self, company_id: int, document_id: int) -> Document | None:
        """
        :return: The document, or None when it does not exist or belongs to another company.
        """
        document = await self._session.get(Document, document_id)
        return (
            document
            if document is not None and document.company_id == company_id
            else None
        )

    async def count_evidence(self, company_id: int) -> dict[int, int]:
        """
        :return: How many documents are linked to each requirement, by requirement id.
        """
        statement = (
            select(Document.requirement_id, func.count())
            .where(
                Document.company_id == company_id, Document.requirement_id.is_not(None)
            )
            .group_by(Document.requirement_id)
        )
        return {
            requirement_id: count
            for requirement_id, count in await self._session.execute(statement)
        }

    async def add(self, document: Document) -> None:
        self._session.add(document)
        await self._session.flush()

    async def delete(self, document: Document) -> None:
        await self._session.delete(document)
