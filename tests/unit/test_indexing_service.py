"""Indexing orchestration unit tests."""

from datetime import UTC, datetime

import pytest

from financial_document_analyst.chunking.text_chunker import TextChunker
from financial_document_analyst.domain.documents import (
    DocumentChunk,
    DocumentType,
    IngestedDocument,
    IngestionResult,
    ParsedDocument,
    ParsedSegment,
    SearchResult,
)
from financial_document_analyst.indexing.service import IndexingError, IndexingService


class FakeEmbeddingProvider:
    name = "fake"
    dimensions = 2

    def __init__(self, embeddings: list[list[float]]) -> None:
        self._embeddings = embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embeddings

    def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0]


class RecordingVectorStore:
    def __init__(self) -> None:
        self.chunks: list[DocumentChunk] = []

    def upsert(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        self.chunks = chunks

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 5,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        return []


def _ingestion_result(content: str = "A restaurant transaction") -> IngestionResult:
    return IngestionResult(
        document=IngestedDocument(
            id="doc-1",
            original_filename="statement.csv",
            document_type=DocumentType.CSV,
            content_type="text/csv",
            size_bytes=20,
            sha256="a" * 64,
            segment_count=1,
            stored_filename="doc-1.csv",
            created_at=datetime.now(UTC),
        ),
        parsed_document=ParsedDocument(
            document_type=DocumentType.CSV,
            segments=[ParsedSegment(content=content, location="row 2")],
        ),
    )


def test_indexing_service_coordinates_components() -> None:
    store = RecordingVectorStore()
    service = IndexingService(
        chunker=TextChunker(chunk_size=100, overlap=0),
        embedding_provider=FakeEmbeddingProvider([[1.0, 0.0]]),
        vector_store=store,
    )

    count = service.index(_ingestion_result())

    assert service.embedding_provider_name == "fake"
    assert count == 1
    assert store.chunks[0].document_id == "doc-1"


@pytest.mark.parametrize("embeddings", [[], [[1.0]], [[1.0, 0.0], [0.0, 1.0]]])
def test_indexing_service_rejects_inconsistent_embeddings(
    embeddings: list[list[float]],
) -> None:
    service = IndexingService(
        chunker=TextChunker(chunk_size=100, overlap=0),
        embedding_provider=FakeEmbeddingProvider(embeddings),
        vector_store=RecordingVectorStore(),
    )

    with pytest.raises(IndexingError):
        service.index(_ingestion_result())
