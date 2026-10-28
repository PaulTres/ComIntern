"""The providers each pluggable resource can be built with, as the environment names them."""

from enum import StrEnum


class LLMProvider(StrEnum):
    OLLAMA = "ollama"


class EmbeddingsProvider(StrEnum):
    FASTEMBED = "fastembed"


class VectorStoreProvider(StrEnum):
    QDRANT = "qdrant"
