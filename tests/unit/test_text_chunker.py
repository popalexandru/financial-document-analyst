"""Text chunker unit tests."""

import pytest

from financial_document_analyst.chunking.text_chunker import (
    InvalidChunkingConfigurationError,
    TextChunker,
)
from financial_document_analyst.domain.documents import (
    DocumentType,
    ParsedDocument,
    ParsedSegment,
)


def test_chunker_preserves_source_and_produces_deterministic_ids() -> None:
    parsed = ParsedDocument(
        document_type=DocumentType.PDF,
        segments=[
            ParsedSegment(
                content="Alpha expense details. Beta expense details. Gamma expense details.",
                location="page 2",
                metadata={"page": 2},
            )
        ],
    )
    chunker = TextChunker(chunk_size=35, overlap=8)

    first_run = chunker.chunk("doc-1", parsed)
    second_run = chunker.chunk("doc-1", parsed)

    assert len(first_run) > 1
    assert [chunk.id for chunk in first_run] == [chunk.id for chunk in second_run]
    assert all(len(chunk.content) <= 35 for chunk in first_run)
    assert all(chunk.location == "page 2" for chunk in first_run)
    assert all(chunk.metadata["source_location"] == "page 2" for chunk in first_run)


def test_chunker_normalizes_whitespace_and_skips_empty_segments() -> None:
    parsed = ParsedDocument(
        document_type=DocumentType.CSV,
        segments=[ParsedSegment(content="  one\n\n two   three  ", location="row 2")],
    )

    chunks = TextChunker(chunk_size=100, overlap=0).chunk("doc-1", parsed)

    assert [chunk.content for chunk in chunks] == ["one two three"]


@pytest.mark.parametrize(
    ("chunk_size", "overlap"),
    [(0, 0), (10, -1), (10, 10), (10, 11)],
)
def test_chunker_rejects_invalid_configuration(chunk_size: int, overlap: int) -> None:
    with pytest.raises(InvalidChunkingConfigurationError):
        TextChunker(chunk_size=chunk_size, overlap=overlap)
