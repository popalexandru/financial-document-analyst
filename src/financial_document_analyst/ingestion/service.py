"""Document ingestion application service."""

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from financial_document_analyst.domain.documents import IngestedDocument, IngestionResult
from financial_document_analyst.ingestion.validators import validate_upload
from financial_document_analyst.parsing.base import DocumentParseError
from financial_document_analyst.parsing.registry import ParserRegistry


class IngestionService:
    """Validate, persist, and parse an uploaded financial document."""

    def __init__(
        self, *, storage_directory: Path, max_upload_size_bytes: int, registry: ParserRegistry
    ) -> None:
        self._storage_directory = storage_directory
        self._max_upload_size_bytes = max_upload_size_bytes
        self._registry = registry

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum number of bytes accepted from an upload stream."""

        return self._max_upload_size_bytes

    def ingest(self, *, filename: str, content_type: str, content: bytes) -> IngestionResult:
        """Store a valid, parseable upload and return its ingestion metadata."""

        document_type = validate_upload(
            filename=filename,
            content_type=content_type,
            content=content,
            max_size_bytes=self._max_upload_size_bytes,
        )
        document_id = str(uuid4())
        stored_filename = f"{document_id}.{document_type.value}"
        stored_path = self._storage_directory / stored_filename
        self._storage_directory.mkdir(parents=True, exist_ok=True)
        stored_path.write_bytes(content)

        try:
            parsed = self._registry.get(document_type).parse(content)
        except DocumentParseError:
            stored_path.unlink(missing_ok=True)
            raise

        return IngestionResult(
            document=IngestedDocument(
                id=document_id,
                original_filename=Path(filename).name,
                document_type=document_type,
                content_type=content_type,
                size_bytes=len(content),
                sha256=sha256(content).hexdigest(),
                segment_count=len(parsed.segments),
                stored_filename=stored_filename,
                created_at=datetime.now(UTC),
            ),
            parsed_document=parsed,
        )
