"""Build the configured embedding model."""

import logging

from langchain_core.embeddings import Embeddings

from comintern.configuration.config import EmbeddingsSettings
from comintern.embedding.fastembed_embedding import FastEmbedEmbedding
from comintern.exceptions import AppError, AppErrorCode
from comintern.models.providers import EmbeddingsProvider

logger = logging.getLogger(__name__)


class EmbeddingFactory:
    @staticmethod
    def create_embedding(embedding_settings: EmbeddingsSettings) -> Embeddings:
        """
        :param embedding_settings: The provider and model.
        :return: The embedding model. FastEmbed downloads it on first use into the cache directory.
        """
        match embedding_settings.provider:
            case EmbeddingsProvider.FASTEMBED:
                logger.info(
                    "Creating FastEmbed model %s", embedding_settings.model_name
                )
                return FastEmbedEmbedding(
                    embedding_settings.model_name,
                    embedding_settings.batch_size,
                    embedding_settings.cache_directory,
                )
            case _:
                logger.error(
                    "Unsupported embeddings provider=%s", embedding_settings.provider
                )
                raise AppError(AppErrorCode.INTERNAL_SERVER_ERROR)
