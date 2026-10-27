"""The providers each pluggable resource can be built with, as the environment names them."""

from enum import StrEnum


class LLMProvider(StrEnum):
    """Chat model provider."""

    OLLAMA = "ollama"


class EmbeddingsProvider(StrEnum):
    """Embedding model provider."""

    FASTEMBED = "fastembed"


class VectorStoreProvider(StrEnum):
    """Vector store provider."""

    QDRANT = "qdrant"
