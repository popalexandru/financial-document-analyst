"""RAG orchestration and citation tests."""

from financial_document_analyst.domain.documents import DocumentChunk, SearchResult
from financial_document_analyst.generation.rag_service import RagService


class StubRetriever:
    def __init__(self, results: list[SearchResult]) -> None:
        self._results = results

    def retrieve(
        self,
        question: str,
        *,
        limit: int,
        minimum_score: float,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        return self._results


class UntrustedGenerator:
    name = "untrusted-test-generator"

    def generate(self, question: str, contexts: list[SearchResult]) -> str:
        return "Generated answer mentioning an unrelated [999]."


def _context() -> SearchResult:
    return SearchResult(
        chunk=DocumentChunk(
            id="trusted-chunk",
            document_id="trusted-document",
            content="Restaurant payment: 86.50 RON",
            location="row 2",
            chunk_index=0,
            metadata={"original_filename": "statement.csv"},
        ),
        score=0.75,
    )


def test_rag_service_builds_citations_from_retrieval_not_generation() -> None:
    service = RagService(
        retriever=StubRetriever([_context()]),
        generator=UntrustedGenerator(),
        default_top_k=5,
        default_minimum_score=0.05,
    )

    response = service.answer("How much was the restaurant payment?")

    assert response.answer.endswith("[999].")
    assert response.retrieved_count == 1
    assert response.citations[0].chunk_id == "trusted-chunk"
    assert response.citations[0].document_id == "trusted-document"
    assert response.citations[0].filename == "statement.csv"
    assert response.citations[0].location == "row 2"


def test_rag_service_does_not_generate_without_evidence() -> None:
    service = RagService(
        retriever=StubRetriever([]),
        generator=UntrustedGenerator(),
        default_top_k=5,
        default_minimum_score=0.05,
    )

    response = service.answer("Unknown question", top_k=2, minimum_score=0.0)

    assert response.retrieved_count == 0
    assert response.citations == []
    assert "No sufficiently relevant evidence" in response.answer
