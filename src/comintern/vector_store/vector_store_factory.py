"""Build the configured vector store, and the few operations LangChain leaves to each provider."""

import logging
from collections.abc import Callable, Collection, Mapping
from typing import Any, NoReturn

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore, VectorStore
from langchain_qdrant import QdrantVectorStore

from comintern.configuration.config import VectorStoreSettings
from comintern.exceptions import AppError, AppErrorCode
from comintern.models.providers import VectorStoreProvider
from comintern.vector_store.qdrant_vector_store import (
    build_qdrant_metadata_filter,
    delete_qdrant_points_by_metadata,
    setup_qdrant_vector_store,
)

logger = logging.getLogger(__name__)


class VectorStoreFactory:
    """Builds the vector store the settings name."""

    @staticmethod
    def create_vector_store(
        embeddings: Embeddings, vector_store_settings: VectorStoreSettings
    ) -> VectorStore:
        """
        :param embeddings: The embedding model the store embeds texts and queries with.
        :param vector_store_settings: The provider and its connection.
        :return: The vector store.
        """
        match vector_store_settings.provider:
            case VectorStoreProvider.QDRANT:
                logger.info("Creating Qdrant vector store")
                return setup_qdrant_vector_store(embeddings, vector_store_settings)
            case _:
                _raise_unsupported(vector_store_settings.provider)


async def delete_points_by_metadata(
    vector_store: VectorStore, metadata_key: str, metadata_value: Any
) -> None:
    """
    Delete every passage whose metadata holds this value; LangChain has no filtered delete.

    :raises AppError: VECTOR_STORE_UNAVAILABLE if the store fails.
    """
    match vector_store:
        case QdrantVectorStore():
            await delete_qdrant_points_by_metadata(
                vector_store, metadata_key, metadata_value
            )
        case InMemoryVectorStore():
            ids = [
                id_
                for id_, point in vector_store.store.items()
                if point["metadata"].get(metadata_key) == metadata_value
            ]
            if ids:
                await vector_store.adelete(ids)
        case _:
            _raise_unsupported(type(vector_store).__name__)


def build_metadata_filter(
    vector_store: VectorStore, metadata_filter: Mapping[str, Any]
) -> Any:
    """
    Build the `filter` a similarity search takes, in the store's own format.

    :param vector_store: The store the filter is for.
    :param metadata_filter: The value each metadata key must hold; a collection means any of its values.
    :return: The filter.
    """
    match vector_store:
        case QdrantVectorStore():
            return build_qdrant_metadata_filter(vector_store, metadata_filter)
        case InMemoryVectorStore():
            return _build_in_memory_filter(metadata_filter)
        case _:
            _raise_unsupported(type(vector_store).__name__)


def _build_in_memory_filter(
    metadata_filter: Mapping[str, Any],
) -> Callable[[Document], bool]:
    def matches(document: Document) -> bool:
        for key, expected in metadata_filter.items():
            actual = document.metadata.get(key)
            if isinstance(expected, Collection) and not isinstance(expected, str):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True

    return matches


def _raise_unsupported(provider: str) -> NoReturn:
    logger.error("Unsupported vector store provider=%s", provider)
    raise AppError(AppErrorCode.INTERNAL_SERVER_ERROR)
