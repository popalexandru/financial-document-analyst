"""Retriever unit tests."""

from financial_document_analyst.domain.documents import (
    DocumentChunk,
    SearchResult,
)
from financial_document_analyst.retrieval.retriever import Retriever


class FakeEmbeddingProvider:
    name = "fake"
    dimensions = 2

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        assert text == "restaurant"
        return [1.0, 0.0]


class FakeVectorStore:
    def __init__(self, results: list[SearchResult]) -> None:
        self._results = results
        self.document_id: str | None = None

    def upsert(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        return None

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 5,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        assert query_embedding == [1.0, 0.0]
        assert limit == 2
        self.document_id = document_id
        return self._results


def _result(chunk_id: str, score: float) -> SearchResult:
    return SearchResult(
        chunk=DocumentChunk(
            id=chunk_id,
            document_id="doc-1",
            content="restaurant payment",
            location="row 2",
            chunk_index=0,
        ),
        score=score,
    )


def test_retriever_embeds_filters_and_forwards_document_scope() -> None:
    store = FakeVectorStore([_result("relevant", 0.8), _result("weak", 0.1)])
    retriever = Retriever(embedding_provider=FakeEmbeddingProvider(), vector_store=store)

    results = retriever.retrieve("restaurant", limit=2, minimum_score=0.5, document_id="doc-1")

    assert [result.chunk.id for result in results] == ["relevant"]
    assert store.document_id == "doc-1"
