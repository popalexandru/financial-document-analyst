"""OpenAI embedding adapter unit tests without network calls."""

from dataclasses import dataclass

import pytest

from financial_document_analyst.embeddings.openai import OpenAIEmbeddingProvider


@dataclass
class FakeEmbeddingItem:
    embedding: list[float]


@dataclass
class FakeEmbeddingResponse:
    data: list[FakeEmbeddingItem]


class FakeEmbeddingsResource:
    def create(self, *, input: list[str], model: str, dimensions: int) -> FakeEmbeddingResponse:
        assert model == "text-embedding-3-small"
        return FakeEmbeddingResponse(
            data=[FakeEmbeddingItem([float(index)] * dimensions) for index, _ in enumerate(input)]
        )


class FakeOpenAIClient:
    embeddings = FakeEmbeddingsResource()


def test_openai_provider_batches_documents_and_embeds_queries() -> None:
    provider = OpenAIEmbeddingProvider(
        api_key="",
        dimensions=3,
        client=FakeOpenAIClient(),
    )

    assert provider.name == "openai:text-embedding-3-small"
    assert provider.dimensions == 3
    assert provider.embed_documents(["one", "two"]) == [
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0],
    ]
    assert provider.embed_query("query") == [0.0, 0.0, 0.0]


def test_openai_provider_requires_key_without_injected_client() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAIEmbeddingProvider(api_key="")


@pytest.mark.parametrize("texts", [[], ["valid", ""]])
def test_openai_provider_rejects_empty_inputs(texts: list[str]) -> None:
    provider = OpenAIEmbeddingProvider(api_key="", client=FakeOpenAIClient())

    with pytest.raises(ValueError, match="non-empty"):
        provider.embed_documents(texts)
