"""Document ingestion domain models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentType(StrEnum):
    """Document formats supported by the ingestion pipeline."""

    PDF = "pdf"
    CSV = "csv"


class ParsedSegment(BaseModel):
    """A source-addressable block of text emitted by a parser."""

    content: str = Field(min_length=1)
    location: str = Field(min_length=1)
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class ParsedDocument(BaseModel):
    """Normalized parser output before chunking and indexing."""

    document_type: DocumentType
    segments: list[ParsedSegment] = Field(min_length=1)
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    """A bounded text unit ready for embedding and retrieval."""

    id: str
    document_id: str
    content: str = Field(min_length=1)
    location: str = Field(min_length=1)
    chunk_index: int = Field(ge=0)
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """A retrieved chunk and its normalized similarity score."""

    chunk: DocumentChunk
    score: float = Field(ge=0.0, le=1.0)


class IngestedDocument(BaseModel):
    """Metadata returned after a document is safely stored and parsed."""

    id: str
    original_filename: str
    document_type: DocumentType
    content_type: str
    size_bytes: int = Field(ge=1)
    sha256: str
    segment_count: int = Field(ge=1)
    chunk_count: int = Field(default=0, ge=0)
    stored_filename: str
    created_at: datetime


class IngestionResult(BaseModel):
    """Internal ingestion result containing both metadata and normalized content."""

    document: IngestedDocument
    parsed_document: ParsedDocument
