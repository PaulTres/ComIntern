"""FastEmbed behind LangChain's `Embeddings`, without the sunset langchain-community package."""

from pathlib import Path

from fastembed import TextEmbedding
from langchain_core.embeddings import Embeddings


class FastEmbedEmbedding(Embeddings):
    """Runs a FastEmbed model locally on the CPU; the model is downloaded once into the cache."""

    def __init__(
        self, model_name: str, batch_size: int, cache_directory: Path | None
    ) -> None:
        self._model = TextEmbedding(
            model_name=model_name,
            cache_dir=str(cache_directory) if cache_directory else None,
        )
        self._batch_size = batch_size

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [
            vector.tolist()
            for vector in self._model.embed(texts, batch_size=self._batch_size)
        ]

    def embed_query(self, text: str) -> list[float]:
        return next(iter(self._model.query_embed(text))).tolist()
