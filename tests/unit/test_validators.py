"""Upload validator unit tests."""

import pytest

from financial_document_analyst.domain.documents import DocumentType
from financial_document_analyst.ingestion.validators import (
    DocumentTooLargeError,
    InvalidDocumentError,
    UnsupportedDocumentError,
    validate_upload,
)


def test_validate_upload_accepts_supported_csv() -> None:
    result = validate_upload(
        filename="statement.CSV",
        content_type="text/csv; charset=utf-8",
        content=b"header\nvalue",
        max_size_bytes=100,
    )

    assert result is DocumentType.CSV


def test_validate_upload_rejects_empty_file() -> None:
    with pytest.raises(InvalidDocumentError, match="empty"):
        validate_upload(
            filename="statement.csv", content_type="text/csv", content=b"", max_size_bytes=10
        )


def test_validate_upload_rejects_oversized_file() -> None:
    with pytest.raises(DocumentTooLargeError):
        validate_upload(
            filename="statement.csv",
            content_type="text/csv",
            content=b"too large",
            max_size_bytes=2,
        )


@pytest.mark.parametrize(
    ("filename", "content_type"),
    [("statement.txt", "text/plain"), ("statement.pdf", "text/csv")],
)
def test_validate_upload_rejects_unsupported_format_or_media_type(
    filename: str, content_type: str
) -> None:
    with pytest.raises(UnsupportedDocumentError):
        validate_upload(
            filename=filename,
            content_type=content_type,
            content=b"content",
            max_size_bytes=100,
        )
