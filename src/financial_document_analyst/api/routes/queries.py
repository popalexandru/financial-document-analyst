"""Retrieval-augmented question answering endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from financial_document_analyst.core.config import Settings, get_settings
from financial_document_analyst.domain.queries import QueryRequest, QueryResponse
from financial_document_analyst.generation.factory import build_rag_service
from financial_document_analyst.generation.rag_service import RagService

router = APIRouter(prefix="/queries", tags=["queries"])


def get_rag_service(settings: Annotated[Settings, Depends(get_settings)]) -> RagService:
    """Build the retrieval and generation pipeline from application settings."""

    return build_rag_service(settings)


@router.post("", response_model=QueryResponse)
def answer_query(
    request: QueryRequest,
    service: Annotated[RagService, Depends(get_rag_service)],
) -> QueryResponse:
    """Answer a question using indexed evidence and return trusted citations."""

    return service.answer(
        request.question,
        document_id=request.document_id,
        top_k=request.top_k,
        minimum_score=request.minimum_score,
    )
