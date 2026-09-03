"""Retrieval-augmented answer orchestration."""

from financial_document_analyst.domain.queries import Citation, QueryResponse
from financial_document_analyst.generation.base import AnswerGenerator
from financial_document_analyst.retrieval.retriever import Retriever


class RagService:
    """Retrieve evidence, generate an answer, and attach trusted provenance."""

    def __init__(
        self,
        *,
        retriever: Retriever,
        generator: AnswerGenerator,
        default_top_k: int,
        default_minimum_score: float,
    ) -> None:
        self._retriever = retriever
        self._generator = generator
        self._default_top_k = default_top_k
        self._default_minimum_score = default_minimum_score

    def answer(
        self,
        question: str,
        *,
        document_id: str | None = None,
        top_k: int | None = None,
        minimum_score: float | None = None,
    ) -> QueryResponse:
        """Answer a question using retrieved context and deterministic citations."""

        contexts = self._retriever.retrieve(
            question,
            limit=top_k or self._default_top_k,
            minimum_score=(
                minimum_score if minimum_score is not None else self._default_minimum_score
            ),
            document_id=document_id,
        )
        if not contexts:
            return QueryResponse(
                answer="No sufficiently relevant evidence was found in the indexed documents.",
                citations=[],
                generator=self._generator.name,
                retrieved_count=0,
            )

        citations = [
            Citation(
                rank=rank,
                chunk_id=result.chunk.id,
                document_id=result.chunk.document_id,
                filename=(
                    str(result.chunk.metadata["original_filename"])
                    if "original_filename" in result.chunk.metadata
                    else None
                ),
                location=result.chunk.location,
                score=result.score,
                excerpt=result.chunk.content[:300],
            )
            for rank, result in enumerate(contexts, start=1)
        ]
        return QueryResponse(
            answer=self._generator.generate(question, contexts),
            citations=citations,
            generator=self._generator.name,
            retrieved_count=len(contexts),
        )
