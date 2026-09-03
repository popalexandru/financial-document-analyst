"""Configuration-driven indexing component assembly."""

import re

from financial_document_analyst.chunking.text_chunker import TextChunker
from financial_document_analyst.core.config import Settings
from financial_document_analyst.embeddings.base import EmbeddingProvider
from financial_document_analyst.embeddings.local import LocalHashEmbeddingProvider
from financial_document_analyst.embeddings.openai import OpenAIEmbeddingProvider
from financial_document_analyst.indexing.service import IndexingService
from financial_document_analyst.vector_store.chroma import ChromaVectorStore


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Create the selected embedding provider from application settings."""

    if settings.embedding_provider == "openai":
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key or "",
            model=settings.openai_embedding_model,
            dimensions=settings.embedding_dimensions,
        )
    return LocalHashEmbeddingProvider(dimensions=settings.embedding_dimensions)


def build_indexing_service(settings: Settings) -> IndexingService:
    """Assemble the indexing pipeline with persistent local vector storage."""

    embedding_provider = build_embedding_provider(settings)
    provider_key = re.sub(r"[^a-zA-Z0-9._-]+", "-", embedding_provider.name)
    collection_name = f"financial-documents-{provider_key}-{settings.embedding_dimensions}"
    return IndexingService(
        chunker=TextChunker(
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        ),
        embedding_provider=embedding_provider,
        vector_store=ChromaVectorStore(
            path=settings.chroma_dir,
            collection_name=collection_name,
        ),
    )
