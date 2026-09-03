"""Text extraction for digitally generated PDF documents."""

import pymupdf

from financial_document_analyst.domain.documents import (
    DocumentType,
    ParsedDocument,
    ParsedSegment,
)
from financial_document_analyst.parsing.base import DocumentParseError


class PdfDocumentParser:
    """Extract one source-addressable text segment per non-empty PDF page."""

    document_type = DocumentType.PDF

    def parse(self, content: bytes) -> ParsedDocument:
        try:
            with pymupdf.open(  # type: ignore[no-untyped-call]
                stream=content, filetype="pdf"
            ) as document:
                if document.needs_pass:
                    raise DocumentParseError("Password-protected PDFs are not supported.")

                segments = [
                    ParsedSegment(
                        content=text,
                        location=f"page {page.number + 1}",
                        metadata={"page": page.number + 1},
                    )
                    for page in document
                    if (text := page.get_text().strip())
                ]
                page_count = document.page_count
        except DocumentParseError:
            raise
        except (pymupdf.FileDataError, RuntimeError) as exc:
            raise DocumentParseError("PDF structure could not be parsed.") from exc

        if not segments:
            raise DocumentParseError(
                "PDF contains no extractable text; scanned PDFs require OCR, "
                "which is not in the MVP."
            )

        return ParsedDocument(
            document_type=self.document_type,
            segments=segments,
            metadata={"page_count": page_count},
        )
