"""Parser protocol and parsing errors."""

from typing import Protocol

from financial_document_analyst.domain.documents import DocumentType, ParsedDocument


class DocumentParseError(ValueError):
    """Raised when a supported file cannot be parsed into useful text."""


class DocumentParser(Protocol):
    """Contract implemented by format-specific document parsers."""

    document_type: DocumentType

    def parse(self, content: bytes) -> ParsedDocument:
        """Parse raw bytes into normalized, source-addressable segments."""
        ...
