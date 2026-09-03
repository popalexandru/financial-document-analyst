"""Parser for UTF-8 CSV transaction exports."""

import csv
import io

from financial_document_analyst.domain.documents import (
    DocumentType,
    ParsedDocument,
    ParsedSegment,
)
from financial_document_analyst.parsing.base import DocumentParseError


class CsvDocumentParser:
    """Convert each non-empty CSV data row into a traceable text segment."""

    document_type = DocumentType.CSV

    def parse(self, content: bytes) -> ParsedDocument:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise DocumentParseError("CSV files must use UTF-8 encoding.") from exc

        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
            reader = csv.DictReader(io.StringIO(text), dialect=dialect)
            if not reader.fieldnames or any(not field.strip() for field in reader.fieldnames):
                raise DocumentParseError("CSV must contain a non-empty header row.")

            segments = [
                ParsedSegment(
                    content=" | ".join(
                        f"{key.strip()}: {(value or '').strip()}"
                        for key, value in row.items()
                        if key is not None
                    ),
                    location=f"row {row_number}",
                    metadata={"row": row_number},
                )
                for row_number, row in enumerate(reader, start=2)
                if any((value or "").strip() for value in row.values())
            ]
        except csv.Error as exc:
            raise DocumentParseError("CSV structure could not be parsed.") from exc

        if not segments:
            raise DocumentParseError("CSV contains no data rows.")

        return ParsedDocument(
            document_type=self.document_type,
            segments=segments,
            metadata={"row_count": len(segments)},
        )
