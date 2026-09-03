"""Format-to-parser lookup."""

from financial_document_analyst.domain.documents import DocumentType
from financial_document_analyst.parsing.base import DocumentParser
from financial_document_analyst.parsing.csv_parser import CsvDocumentParser
from financial_document_analyst.parsing.pdf_parser import PdfDocumentParser


class ParserRegistry:
    """Select a parser without coupling ingestion to parser implementations."""

    def __init__(self, parsers: list[DocumentParser] | None = None) -> None:
        configured_parsers = parsers or [CsvDocumentParser(), PdfDocumentParser()]
        self._parsers = {parser.document_type: parser for parser in configured_parsers}

    def get(self, document_type: DocumentType) -> DocumentParser:
        """Return the parser registered for a supported document type."""

        return self._parsers[document_type]
