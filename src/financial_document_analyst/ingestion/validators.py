"""Upload validation independent of the HTTP layer."""

from pathlib import Path

from financial_document_analyst.domain.documents import DocumentType


class UnsupportedDocumentError(ValueError):
    """Raised when an uploaded document format or media type is unsupported."""


class InvalidDocumentError(ValueError):
    """Raised when an upload is empty or otherwise invalid."""


class DocumentTooLargeError(InvalidDocumentError):
    """Raised when an upload exceeds the configured size limit."""


SUPPORTED_DOCUMENTS: dict[str, tuple[DocumentType, frozenset[str]]] = {
    ".csv": (
        DocumentType.CSV,
        frozenset({"text/csv", "application/csv", "application/vnd.ms-excel"}),
    ),
    ".pdf": (DocumentType.PDF, frozenset({"application/pdf"})),
}


def validate_upload(
    *, filename: str, content_type: str, content: bytes, max_size_bytes: int
) -> DocumentType:
    """Validate upload metadata and bytes, returning its canonical document type."""

    if not content:
        raise InvalidDocumentError("Uploaded document is empty.")
    if len(content) > max_size_bytes:
        raise DocumentTooLargeError(f"Uploaded document exceeds the {max_size_bytes} byte limit.")

    suffix = Path(filename).suffix.lower()
    supported = SUPPORTED_DOCUMENTS.get(suffix)
    if supported is None:
        raise UnsupportedDocumentError("Only PDF and CSV documents are supported.")

    document_type, allowed_content_types = supported
    normalized_content_type = content_type.lower().split(";", maxsplit=1)[0].strip()
    if normalized_content_type not in allowed_content_types:
        raise UnsupportedDocumentError(
            f"Content type '{content_type}' does not match a {suffix} document."
        )
    return document_type
