"""CSV parser unit tests."""

import pytest

from financial_document_analyst.domain.documents import DocumentType
from financial_document_analyst.parsing.base import DocumentParseError
from financial_document_analyst.parsing.csv_parser import CsvDocumentParser


def test_csv_parser_emits_traceable_rows() -> None:
    content = b"date,description,amount\n2026-08-01,Coffee,-12.50\n"

    parsed = CsvDocumentParser().parse(content)

    assert parsed.document_type is DocumentType.CSV
    assert parsed.metadata == {"row_count": 1}
    assert parsed.segments[0].location == "row 2"
    assert "description: Coffee" in parsed.segments[0].content


@pytest.mark.parametrize("content", [b"", b"date,amount\n"])
def test_csv_parser_rejects_files_without_data_rows(content: bytes) -> None:
    with pytest.raises(DocumentParseError):
        CsvDocumentParser().parse(content)


def test_csv_parser_rejects_non_utf8_content() -> None:
    with pytest.raises(DocumentParseError, match="UTF-8"):
        CsvDocumentParser().parse(b"description\n\xff")
