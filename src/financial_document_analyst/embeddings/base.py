"""Embedding provider contract."""

from typing import Protocol


class EmbeddingProvider(Protocol):
    """Convert document and query text into vectors in the same vector space."""

    @property
    def dimensions(self) -> int:
        """Return the fixed vector dimensionality produced by this provider."""
        ...

    @property
    def name(self) -> str:
        """Return a stable provider identifier for observability."""
        ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of non-empty document texts."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed one non-empty search query."""
        ...
