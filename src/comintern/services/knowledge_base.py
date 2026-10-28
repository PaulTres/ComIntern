"""The passages the assistant searches: the catalog, the official regulation texts and each
company's own evidence."""

import logging
from uuid import NAMESPACE_URL, uuid5

from langchain_core.vectorstores import VectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from comintern.configuration.config import ChunkingSettings
from comintern.exceptions import AppError, AppErrorCode
from comintern.models.knowledge import PUBLIC_COMPANY_ID, Chunk, PassageKind
from comintern.vector_store.vector_store_factory import (
    build_metadata_filter,
    delete_points_by_metadata,
)

logger = logging.getLogger(__name__)

SOURCE_ID_KEY = "source_id"


class KnowledgeBase:
    """Cuts texts into passages, stores them in the vector store and searches them."""

    def __init__(
        self, vector_store: VectorStore, chunking_settings: ChunkingSettings
    ) -> None:
        self._vector_store = vector_store
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunking_settings.chunk_size,
            chunk_overlap=chunking_settings.chunk_overlap,
        )

    async def index(
        self,
        source_id: str,
        title: str,
        text: str,
        *,
        kind: PassageKind,
        company_id: int = PUBLIC_COMPANY_ID,
        regulation_code: str | None = None,
    ) -> int:
        """
        Replace the passages of one source. Running it twice leaves the same passages.

        :param source_id: Identifies the source, e.g. evidence:42.
        :param title: The title shown when an answer cites it.
        :param text: The full text.
        :param kind: Where the text comes from.
        :param company_id: The company that may read it; PUBLIC_COMPANY_ID for everyone.
        :param regulation_code: The regulation it belongs to, if any.
        :return: How many passages were stored.
        :raises AppError: VECTOR_STORE_UNAVAILABLE if the store fails.
        """
        await self.remove(source_id)
        # Every passage starts with its source's title, so a passage from the middle of a law
        # still says which law it is: without it, the requirement lists of different laws look alike.
        passages = [f"{title}\n{piece}" for piece in self._splitter.split_text(text)]
        if not passages:
            return 0
        metadatas = [
            {
                SOURCE_ID_KEY: source_id,
                "title": title,
                "kind": kind.value,
                "company_id": company_id,
                "regulation_code": regulation_code or "",
                "chunk_index": index,
            }
            for index in range(len(passages))
        ]
        ids = [
            str(uuid5(NAMESPACE_URL, f"{source_id}#{index}"))
            for index in range(len(passages))
        ]
        try:
            await self._vector_store.aadd_texts(passages, metadatas=metadatas, ids=ids)
        except Exception as error:
            logger.exception("The vector store could not index source=%s", source_id)
            raise AppError(AppErrorCode.VECTOR_STORE_UNAVAILABLE) from error
        logger.info("Indexed %s passages of source=%s", len(passages), source_id)
        return len(passages)

    async def remove(self, source_id: str) -> None:
        await delete_points_by_metadata(self._vector_store, SOURCE_ID_KEY, source_id)

    async def search(
        self,
        query: str,
        company_id: int,
        top_k: int,
        min_score: float,
        regulation_code: str | None = None,
    ) -> list[Chunk]:
        """
        Find the passages closest to the query that this company may read.

        :param query: What to search for.
        :param company_id: The company asking; it reads the public passages and its own.
        :param top_k: At most this many passages.
        :param min_score: Passages scoring below it are dropped.
        :param regulation_code: Only the passages of this regulation.
        :return: The passages, best first.
        :raises AppError: VECTOR_STORE_UNAVAILABLE if the store fails.
        """
        conditions: dict[str, object] = {"company_id": [PUBLIC_COMPANY_ID, company_id]}
        if regulation_code:
            conditions["regulation_code"] = regulation_code
        try:
            scored_documents = (
                await self._vector_store.asimilarity_search_with_relevance_scores(
                    query,
                    k=top_k,
                    filter=build_metadata_filter(self._vector_store, conditions),
                )
            )
        except Exception as error:
            logger.exception("The vector store could not run the search")
            raise AppError(AppErrorCode.VECTOR_STORE_UNAVAILABLE) from error
        chunks = [
            Chunk(
                source_id=document.metadata[SOURCE_ID_KEY],
                title=document.metadata["title"],
                chunk_index=document.metadata["chunk_index"],
                text=document.page_content,
                score=score,
            )
            for document, score in scored_documents
            if score >= min_score
        ]
        logger.info(
            "Search found %s passages, %s at or above the minimum score",
            len(scored_documents),
            len(chunks),
        )
        return chunks
