"""Persistent Chroma adapter integration tests."""

from pathlib import Path

import pytest

from financial_document_analyst.domain.documents import DocumentChunk
from financial_document_analyst.vector_store.chroma import (
    ChromaVectorStore,
    VectorStoreDataError,
)


def _chunk(chunk_id: str, document_id: str, content: str) -> DocumentChunk:
    return DocumentChunk(
        id=chunk_id,
        document_id=document_id,
        content=content,
        location="row 2",
        chunk_index=0,
        metadata={"row": 2},
    )


def test_chroma_store_persists_and_searches_precomputed_vectors(tmp_path: Path) -> None:
    path = tmp_path / "chroma"
    store = ChromaVectorStore(path=path, collection_name="test-collection")
    store.upsert(
        [
            _chunk("chunk-1", "doc-1", "restaurant payment"),
            _chunk("chunk-2", "doc-2", "salary income"),
        ],
        [[1.0, 0.0], [0.0, 1.0]],
    )

    reopened_store = ChromaVectorStore(path=path, collection_name="test-collection")
    results = reopened_store.search([1.0, 0.0], limit=2)
    filtered = reopened_store.search([1.0, 0.0], limit=2, document_id="doc-2")

    assert results[0].chunk.id == "chunk-1"
    assert results[0].score == pytest.approx(1.0)
    assert results[0].chunk.metadata == {"row": 2}
    assert [result.chunk.document_id for result in filtered] == ["doc-2"]


def test_chroma_store_validates_batches_and_queries(tmp_path: Path) -> None:
    store = ChromaVectorStore(path=tmp_path / "chroma", collection_name="validation-test")

    store.upsert([], [])
    assert store.search([1.0, 0.0]) == []
    with pytest.raises(VectorStoreDataError, match="exactly one"):
        store.upsert([_chunk("chunk-1", "doc-1", "content")], [])
    with pytest.raises(VectorStoreDataError, match="positive"):
        store.search([1.0, 0.0], limit=0)
