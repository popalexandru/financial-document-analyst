"""Question-answering API and domain models."""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """A natural-language question and optional retrieval constraints."""

    question: str = Field(min_length=2, max_length=2_000)
    document_id: str | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)
    minimum_score: float | None = Field(default=None, ge=0.0, le=1.0)


class Citation(BaseModel):
    """Application-generated provenance for one retrieved source chunk."""

    rank: int = Field(ge=1)
    chunk_id: str
    document_id: str
    filename: str | None = None
    location: str
    score: float = Field(ge=0.0, le=1.0)
    excerpt: str


class QueryResponse(BaseModel):
    """A grounded answer with independently constructed source citations."""

    answer: str
    citations: list[Citation]
    generator: str
    retrieved_count: int = Field(ge=0)
