"""Persistent Chroma vector store adapter."""

from pathlib import Path
from typing import Any, cast

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.api.types import Embeddings
from chromadb.config import Settings as ChromaSettings

from financial_document_analyst.domain.documents import DocumentChunk, SearchResult


class VectorStoreDataError(ValueError):
    """Raised when chunks and embeddings do not form a valid index batch."""


class ChromaVectorStore:
    """Store caller-provided embeddings in a local persistent Chroma collection."""

    def __init__(self, *, path: Path, collection_name: str = "financial-documents") -> None:
        path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(
            path=str(path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection: Collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=None,
        )

    def upsert(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise VectorStoreDataError("Each chunk must have exactly one embedding.")

        self._collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            embeddings=cast(Embeddings, embeddings),
            metadatas=[
                {
                    **chunk.metadata,
                    "document_id": chunk.document_id,
                    "location": chunk.location,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ],
        )

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 5,
        document_id: str | None = None,
    ) -> list[SearchResult]:
        if limit < 1:
            raise VectorStoreDataError("Search limit must be positive.")
        if self._collection.count() == 0:
            return []

        raw_results = self._collection.query(
            query_embeddings=cast(Embeddings, [query_embedding]),
            n_results=limit,
            where={"document_id": document_id} if document_id else None,
            include=["documents", "metadatas", "distances"],
        )
        ids = (raw_results.get("ids") or [[]])[0]
        documents = (raw_results.get("documents") or [[]])[0]
        metadatas = (raw_results.get("metadatas") or [[]])[0]
        distances = (raw_results.get("distances") or [[]])[0]

        results: list[SearchResult] = []
        for chunk_id, content, raw_metadata, distance in zip(
            ids, documents, metadatas, distances, strict=True
        ):
            if content is None or raw_metadata is None or distance is None:
                continue
            metadata = cast(dict[str, Any], raw_metadata)
            document_id_value = str(metadata.pop("document_id"))
            location = str(metadata.pop("location"))
            chunk_index = int(metadata.pop("chunk_index"))
            results.append(
                SearchResult(
                    chunk=DocumentChunk(
                        id=chunk_id,
                        document_id=document_id_value,
                        content=content,
                        location=location,
                        chunk_index=chunk_index,
                        metadata=metadata,
                    ),
                    score=max(0.0, min(1.0, 1.0 - float(distance))),
                )
            )
        return results
