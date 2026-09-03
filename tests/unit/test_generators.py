"""Local and OpenAI answer generator tests."""

from dataclasses import dataclass

import pytest

from financial_document_analyst.domain.documents import DocumentChunk, SearchResult
from financial_document_analyst.generation.local import LocalExtractiveGenerator
from financial_document_analyst.generation.openai import OpenAIAnswerGenerator


def _context() -> SearchResult:
    return SearchResult(
        chunk=DocumentChunk(
            id="chunk-1",
            document_id="doc-1",
            content="Coffee payment: 12.50 RON",
            location="row 2",
            chunk_index=0,
        ),
        score=0.8,
    )


@dataclass
class FakeResponse:
    output_text: str


class FakeResponsesResource:
    def __init__(self, output_text: str = "The payment was 12.50 RON [1].") -> None:
        self.output_text = output_text
        self.last_input = ""
        self.store: bool | None = None

    def create(
        self,
        *,
        model: str,
        instructions: str,
        input: str,
        store: bool,
    ) -> FakeResponse:
        assert model == "test-model"
        assert "Use only" in instructions
        self.last_input = input
        self.store = store
        return FakeResponse(self.output_text)


class FakeOpenAIClient:
    def __init__(self, responses: FakeResponsesResource) -> None:
        self.responses = responses


def test_local_generator_returns_ranked_evidence() -> None:
    generator = LocalExtractiveGenerator()

    answer = generator.generate("How much?", [_context()])

    assert generator.name == "local-extractive"
    assert "[1] Coffee payment: 12.50 RON" in answer


def test_openai_generator_sends_grounded_context_without_storage() -> None:
    responses = FakeResponsesResource()
    generator = OpenAIAnswerGenerator(
        api_key="", model="test-model", client=FakeOpenAIClient(responses)
    )

    answer = generator.generate("How much?", [_context()])

    assert answer == "The payment was 12.50 RON [1]."
    assert generator.name == "openai:test-model"
    assert "document_id: doc-1" in responses.last_input
    assert "location: row 2" in responses.last_input
    assert responses.store is False


def test_openai_generator_requires_api_key_without_client() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAIAnswerGenerator(api_key="", model="test-model")


def test_openai_generator_rejects_empty_response() -> None:
    responses = FakeResponsesResource(output_text="  ")
    generator = OpenAIAnswerGenerator(
        api_key="", model="test-model", client=FakeOpenAIClient(responses)
    )

    with pytest.raises(RuntimeError, match="empty answer"):
        generator.generate("How much?", [_context()])
