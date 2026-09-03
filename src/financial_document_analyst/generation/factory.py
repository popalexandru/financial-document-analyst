"""Configuration-driven RAG component assembly."""

from financial_document_analyst.core.config import Settings
from financial_document_analyst.generation.base import AnswerGenerator
from financial_document_analyst.generation.local import LocalExtractiveGenerator
from financial_document_analyst.generation.openai import OpenAIAnswerGenerator
from financial_document_analyst.generation.rag_service import RagService
from financial_document_analyst.indexing.factory import (
    build_embedding_provider,
    build_vector_store,
)
from financial_document_analyst.retrieval.retriever import Retriever


def build_answer_generator(settings: Settings) -> AnswerGenerator:
    """Create the selected answer generator from application settings."""

    if settings.generation_provider == "openai":
        return OpenAIAnswerGenerator(
            api_key=settings.openai_api_key or "",
            model=settings.openai_generation_model,
        )
    return LocalExtractiveGenerator()


def build_rag_service(settings: Settings) -> RagService:
    """Assemble retrieval and generation over the active embedding collection."""

    embedding_provider = build_embedding_provider(settings)
    return RagService(
        retriever=Retriever(
            embedding_provider=embedding_provider,
            vector_store=build_vector_store(settings, embedding_provider),
        ),
        generator=build_answer_generator(settings),
        default_top_k=settings.rag_top_k,
        default_minimum_score=settings.rag_minimum_score,
    )
