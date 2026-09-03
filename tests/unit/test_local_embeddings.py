"""Local embedding provider unit tests."""

import math

import pytest

from financial_document_analyst.embeddings.local import LocalHashEmbeddingProvider


def test_local_embeddings_are_normalized_and_deterministic() -> None:
    provider = LocalHashEmbeddingProvider(dimensions=64)

    document_vector = provider.embed_documents(["restaurant payment"])[0]
    query_vector = provider.embed_query("restaurant payment")

    assert provider.name == "local-hash"
    assert provider.dimensions == 64
    assert document_vector == query_vector
    assert math.sqrt(sum(value * value for value in query_vector)) == pytest.approx(1.0)


@pytest.mark.parametrize("text", ["", "   ", "!!!"])
def test_local_embeddings_reject_text_without_tokens(text: str) -> None:
    with pytest.raises(ValueError):
        LocalHashEmbeddingProvider().embed_query(text)


def test_local_embeddings_reject_invalid_dimensions() -> None:
    with pytest.raises(ValueError, match="dimensions"):
        LocalHashEmbeddingProvider(dimensions=0)
