"""OpenAI embeddings adapter."""

from typing import Protocol, cast

from openai import OpenAI


class _EmbeddingItem(Protocol):
    embedding: list[float]


class _EmbeddingResponse(Protocol):
    data: list[_EmbeddingItem]


class _EmbeddingsResource(Protocol):
    def create(self, *, input: list[str], model: str, dimensions: int) -> _EmbeddingResponse: ...


class _OpenAIClient(Protocol):
    embeddings: _EmbeddingsResource


class OpenAIEmbeddingProvider:
    """Produce embeddings in batches through the OpenAI embeddings endpoint."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int = 256,
        client: _OpenAIClient | None = None,
    ) -> None:
        if not api_key and client is None:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI embedding provider.")
        self._model = model
        self._dimensions = dimensions
        self._client = client or cast(_OpenAIClient, OpenAI(api_key=api_key))

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def name(self) -> str:
        return f"openai:{self._model}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts or any(not text.strip() for text in texts):
            raise ValueError("Embedding input must contain non-empty texts.")
        response = self._client.embeddings.create(
            input=texts,
            model=self._model,
            dimensions=self._dimensions,
        )
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
