"""Application settings, read from the environment and `.env`.

Nested groups use the `__` delimiter: `DATABASE__URL`, `LLM__MODEL_NAME`. Every key is listed
in `.env.example`.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict

from comintern.models.providers import (
    EmbeddingsProvider,
    LLMProvider,
    VectorStoreProvider,
)


class DatabaseSettings(BaseModel):
    """PostgreSQL connection."""

    url: str = Field(
        description="Async SQLAlchemy URL, e.g. postgresql+asyncpg://user:password@host:5432/name"
    )
    pool_size: PositiveInt = Field(
        default=5, description="Connections kept open in the pool."
    )
    max_overflow: NonNegativeInt = Field(
        default=10, description="Extra connections allowed above the pool size."
    )


class LoggingSettings(BaseModel):
    """Logging."""

    level: str = Field(
        default="INFO",
        description="Python logging level: DEBUG, INFO, WARNING or ERROR.",
    )


class RunAppSettings(BaseModel):
    """Where the API listens."""

    host: str = Field(default="127.0.0.1", description="Interface the API binds to.")
    port: PositiveInt = Field(default=8000, description="Port the API listens on.")


class CorsSettings(BaseModel):
    """Browsers allowed to call the API."""

    origins: list[str] = Field(
        default=["http://localhost:3000"], description="Allowed frontend origins."
    )


class JWTSettings(BaseModel):
    """Access tokens."""

    secret_key: str = Field(
        min_length=32, description="Signs the access tokens; keep it secret."
    )
    algorithm: str = Field(default="HS256", description="JWT signing algorithm.")
    expire_minutes: PositiveInt = Field(
        default=60 * 24, description="How long a login stays valid."
    )


class DocumentsSettings(BaseModel):
    """Uploaded evidence and the official regulation texts."""

    upload_directory: Path = Field(
        description="Where uploaded evidence files are stored, one folder per company."
    )
    regulation_texts_directory: Path = Field(
        description="Official regulation texts to index, one subfolder per regulation code, e.g. EU_GDPR/."
    )
    max_file_size_bytes: PositiveInt = Field(
        default=25 * 1024 * 1024, description="Largest accepted upload."
    )
    allowed_extensions: list[str] = Field(
        default=[
            ".pdf",
            ".docx",
            ".doc",
            ".xlsx",
            ".xls",
            ".pptx",
            ".txt",
            ".md",
            ".csv",
            ".png",
            ".jpg",
            ".jpeg",
        ],
        description="File types accepted as evidence; text is extracted from .pdf, .docx, .txt, .md and .csv.",
    )


class ChunkingSettings(BaseModel):
    """How texts are cut into passages before they are embedded."""

    chunk_size: PositiveInt = Field(
        default=1200, description="Maximum characters per passage."
    )
    chunk_overlap: NonNegativeInt = Field(
        default=150, description="Characters repeated between neighbouring passages."
    )


class VectorStoreSettings(BaseModel):
    """Vector store holding the passages."""

    provider: Literal[VectorStoreProvider.QDRANT] = VectorStoreProvider.QDRANT
    url: str = Field(description="Qdrant URL, e.g. http://localhost:6333")
    collection_name: str = Field(
        description="Qdrant collection; it must exist before the app starts."
    )
    timeout_seconds: PositiveInt = Field(
        default=30, description="Longest wait for one Qdrant request."
    )


class EmbeddingsSettings(BaseModel):
    """Embedding model."""

    provider: Literal[EmbeddingsProvider.FASTEMBED] = EmbeddingsProvider.FASTEMBED
    model_name: str = Field(
        description="FastEmbed model; it must cover English, German and Romanian."
    )
    size: PositiveInt = Field(
        description="Vector size of the model; the Qdrant collection uses the same."
    )
    batch_size: PositiveInt = Field(default=32, description="Texts embedded per batch.")
    cache_directory: Path | None = Field(
        default=None,
        description="Where the model is downloaded once; empty means the system temp folder.",
    )


class LLMSettings(BaseModel):
    """Chat model."""

    provider: Literal[LLMProvider.OLLAMA] = LLMProvider.OLLAMA
    model_name: str = Field(
        description="Ollama model, e.g. gemma4:12b; it must support tool calling."
    )
    base_url: str = Field(description="Ollama URL, e.g. http://localhost:11434")
    temperature: float = Field(
        default=0.2, ge=0, le=2, description="Sampling temperature."
    )
    max_tokens: PositiveInt = Field(
        default=1024, description="Longest answer, in tokens."
    )
    timeout_seconds: PositiveInt = Field(
        default=180, description="Longest wait for one model call."
    )
    reasoning: bool = Field(
        default=False,
        description="Let a thinking model (e.g. gemma4) think before it answers: "
        "better on hard questions, about ten times slower on a laptop.",
    )


class OrchestratorAgentSettings(BaseModel):
    """Orchestrator agent."""

    max_recursion_limit: PositiveInt = Field(
        default=8, description="Most graph steps the orchestrator may take."
    )


class KnowledgeAgentSettings(BaseModel):
    """Knowledge agent."""

    max_recursion_limit: PositiveInt = Field(
        default=12, description="Most steps the retrieval agent may take."
    )
    top_k: PositiveInt = Field(default=6, description="Passages returned per search.")
    similarity_score: float = Field(
        default=0.3, ge=0, le=1, description="Passages scoring below it are dropped."
    )
    history_turns: PositiveInt = Field(
        default=3, description="Earlier turns of the conversation kept as context."
    )
    chunk_preview_length: PositiveInt = Field(
        default=400, description="Characters of a passage the retrieval agent reads."
    )


class RegulationAgentSettings(BaseModel):
    """Regulation agent."""

    top_k: PositiveInt = Field(
        default=4, description="Passages of the regulation's texts added to the answer."
    )
    similarity_score: float = Field(
        default=0.3, ge=0, le=1, description="Passages scoring below it are dropped."
    )
    history_turns: PositiveInt = Field(
        default=3, description="Earlier turns of the conversation kept as context."
    )


class Settings(BaseSettings):
    """All settings of the application."""

    database: DatabaseSettings
    logging: LoggingSettings = LoggingSettings()
    run: RunAppSettings = RunAppSettings()
    cors: CorsSettings = CorsSettings()
    jwt: JWTSettings
    documents: DocumentsSettings
    chunking: ChunkingSettings = ChunkingSettings()
    vector_store: VectorStoreSettings
    embeddings: EmbeddingsSettings
    llm: LLMSettings
    orchestrator_agent: OrchestratorAgentSettings = OrchestratorAgentSettings()
    knowledge_agent: KnowledgeAgentSettings = KnowledgeAgentSettings()
    regulation_agent: RegulationAgentSettings = RegulationAgentSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Read the settings once and reuse them.

    :return: The application settings.
    """
    return Settings()
