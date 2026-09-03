"""Vector store contract."""

from typing import Protocol

from financial_document_analyst.domain.documents import DocumentChunk, SearchResult


class VectorStore(Protocol):
    """Persist embedded chunks and perform nearest-neighbor search."""

    def upsert(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        """Insert or replace chunks and their precomputed embeddings."""
        ...

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 5,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        """Return the closest chunks, optionally restricted to one document."""
        ...
