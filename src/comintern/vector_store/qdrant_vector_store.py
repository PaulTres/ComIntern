import asyncio
import logging
from collections.abc import Collection, Mapping
from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import models
from qdrant_client.http.exceptions import ApiException

from comintern.configuration.config import VectorStoreSettings
from comintern.exceptions import AppError, AppErrorCode

logger = logging.getLogger(__name__)


def setup_qdrant_vector_store(
    embeddings: Embeddings, vector_store_settings: VectorStoreSettings
) -> QdrantVectorStore:
    """
    Connect to the existing collection; `qdrant-init` in docker-compose creates it.

    :param embeddings: The embedding model.
    :param vector_store_settings: The Qdrant URL, collection and timeout.
    :return: The Qdrant vector store.
    """
    return QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        url=vector_store_settings.url,
        collection_name=vector_store_settings.collection_name,
        timeout=vector_store_settings.timeout_seconds,
    )


async def delete_qdrant_points_by_metadata(
    vector_store: QdrantVectorStore, metadata_key: str, metadata_value: Any
) -> None:
    """
    :raises AppError: VECTOR_STORE_UNAVAILABLE if Qdrant fails.
    """
    metadata_filter = build_qdrant_metadata_filter(
        vector_store, {metadata_key: metadata_value}
    )
    try:
        await asyncio.to_thread(
            vector_store.client.delete,
            collection_name=vector_store.collection_name,
            points_selector=models.FilterSelector(filter=metadata_filter),
            wait=True,
        )
    except ApiException as error:
        logger.exception(
            "Qdrant could not delete the points where %s matches", metadata_key
        )
        raise AppError(AppErrorCode.VECTOR_STORE_UNAVAILABLE) from error


def build_qdrant_metadata_filter(
    vector_store: QdrantVectorStore, metadata_filter: Mapping[str, Any]
) -> models.Filter:
    """
    :param vector_store: The Qdrant store; gives where the metadata sits in a point's payload.
    :param metadata_filter: The value each metadata key must hold; a collection means any of its values.
    :return: A filter requiring every condition.
    """
    conditions = []
    for metadata_key, metadata_value in metadata_filter.items():
        if isinstance(metadata_value, Collection) and not isinstance(
            metadata_value, str
        ):
            match: models.Match = models.MatchAny(any=list(metadata_value))
        else:
            match = models.MatchValue(value=metadata_value)
        conditions.append(
            models.FieldCondition(
                key=f"{vector_store.metadata_payload_key}.{metadata_key}", match=match
            )
        )
    return models.Filter(must=conditions)
