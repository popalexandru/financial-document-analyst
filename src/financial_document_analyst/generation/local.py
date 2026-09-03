"""Deterministic offline answer generation."""

from financial_document_analyst.domain.documents import SearchResult


class LocalExtractiveGenerator:
    """Return ranked evidence verbatim for a fully offline RAG demonstration."""

    @property
    def name(self) -> str:
        return "local-extractive"

    def generate(self, question: str, contexts: list[SearchResult]) -> str:
        del question
        evidence = "\n".join(
            f"[{rank}] {result.chunk.content}" for rank, result in enumerate(contexts, start=1)
        )
        return f"Relevant evidence from the uploaded documents:\n{evidence}"
