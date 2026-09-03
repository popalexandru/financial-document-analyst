"""Answer generator contract."""

from typing import Protocol

from financial_document_analyst.domain.documents import SearchResult


class AnswerGenerator(Protocol):
    """Generate an answer using only caller-supplied retrieved evidence."""

    @property
    def name(self) -> str:
        """Return a stable generator identifier."""
        ...

    def generate(self, question: str, contexts: list[SearchResult]) -> str:
        """Generate a grounded answer for a question and ranked contexts."""
        ...
