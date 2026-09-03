"""Semantic retrieval over the configured vector store."""

from financial_document_analyst.domain.documents import SearchResult
from financial_document_analyst.embeddings.base import EmbeddingProvider
from financial_document_analyst.vector_store.base import VectorStore


class Retriever:
    """Embed a question and return relevant indexed chunks."""

    def __init__(self, *, embedding_provider: EmbeddingProvider, vector_store: VectorStore) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def retrieve(
        self,
        question: str,
        *,
        limit: int,
        minimum_score: float,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        """Retrieve and threshold results for a natural-language question."""

        query_embedding = self._embedding_provider.embed_query(question)
        candidates = self._vector_store.search(
            query_embedding,
            limit=limit,
            document_id=document_id,
        )
        return [result for result in candidates if result.score >= minimum_score]
