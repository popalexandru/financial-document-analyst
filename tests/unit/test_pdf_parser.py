"""PDF parser unit tests."""

import pymupdf
import pytest

from financial_document_analyst.domain.documents import DocumentType
from financial_document_analyst.parsing.base import DocumentParseError
from financial_document_analyst.parsing.pdf_parser import PdfDocumentParser


def _create_pdf(text: str | None = None) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def test_pdf_parser_emits_traceable_pages() -> None:
    parsed = PdfDocumentParser().parse(_create_pdf("Invoice total: 120.00 RON"))

    assert parsed.document_type is DocumentType.PDF
    assert parsed.metadata == {"page_count": 1}
    assert parsed.segments[0].location == "page 1"
    assert "120.00 RON" in parsed.segments[0].content


def test_pdf_parser_rejects_invalid_pdf() -> None:
    with pytest.raises(DocumentParseError, match="structure"):
        PdfDocumentParser().parse(b"not a pdf")


def test_pdf_parser_rejects_pdf_without_text() -> None:
    with pytest.raises(DocumentParseError, match="no extractable text"):
        PdfDocumentParser().parse(_create_pdf())
