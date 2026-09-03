"""Chunk, embed, and index parsed documents."""

from financial_document_analyst.chunking.text_chunker import TextChunker
from financial_document_analyst.domain.documents import IngestionResult
from financial_document_analyst.embeddings.base import EmbeddingProvider
from financial_document_analyst.vector_store.base import VectorStore


class IndexingError(RuntimeError):
    """Raised when an indexing component returns an inconsistent result."""


class IndexingService:
    """Coordinate chunking, embedding, and persistent vector storage."""

    def __init__(
        self,
        *,
        chunker: TextChunker,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._chunker = chunker
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    @property
    def embedding_provider_name(self) -> str:
        """Expose the configured provider for diagnostics and future health checks."""

        return self._embedding_provider.name

    def index(self, result: IngestionResult) -> int:
        """Index a parsed document and return the number of stored chunks."""

        chunks = self._chunker.chunk(result.document.id, result.parsed_document)
        if not chunks:
            raise IndexingError("The parsed document produced no indexable chunks.")
        embeddings = self._embedding_provider.embed_documents([chunk.content for chunk in chunks])
        if len(embeddings) != len(chunks):
            raise IndexingError("Embedding provider returned an unexpected vector count.")
        if any(len(embedding) != self._embedding_provider.dimensions for embedding in embeddings):
            raise IndexingError("Embedding provider returned an unexpected vector dimension.")
        self._vector_store.upsert(chunks, embeddings)
        return len(chunks)
