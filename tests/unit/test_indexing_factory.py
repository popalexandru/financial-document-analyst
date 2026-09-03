"""Indexing factory tests."""

from pathlib import Path

import pytest

from financial_document_analyst.core.config import Settings
from financial_document_analyst.embeddings.local import LocalHashEmbeddingProvider
from financial_document_analyst.indexing.factory import (
    build_embedding_provider,
    build_indexing_service,
)


def test_factory_builds_offline_indexing_pipeline(tmp_path: Path) -> None:
    settings = Settings(
        chroma_dir=tmp_path / "chroma",
        embedding_provider="local",
        embedding_dimensions=32,
    )

    provider = build_embedding_provider(settings)
    service = build_indexing_service(settings)

    assert isinstance(provider, LocalHashEmbeddingProvider)
    assert service.embedding_provider_name == "local-hash"


def test_factory_requires_key_for_openai_provider() -> None:
    settings = Settings(embedding_provider="openai", openai_api_key=None)

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        build_embedding_provider(settings)
