"""Document upload endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from financial_document_analyst.core.config import Settings, get_settings
from financial_document_analyst.domain.documents import IngestedDocument
from financial_document_analyst.extraction.transactions import (
    CsvTransactionExtractor,
    StructuredExtractionService,
)
from financial_document_analyst.indexing.factory import build_indexing_service
from financial_document_analyst.indexing.service import IndexingService
from financial_document_analyst.ingestion.service import IngestionService
from financial_document_analyst.ingestion.validators import (
    DocumentTooLargeError,
    InvalidDocumentError,
    UnsupportedDocumentError,
)
from financial_document_analyst.parsing.base import DocumentParseError
from financial_document_analyst.parsing.registry import ParserRegistry
from financial_document_analyst.persistence.transactions import TransactionRepository

router = APIRouter(prefix="/documents", tags=["documents"])


def get_ingestion_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> IngestionService:
    """Build the ingestion service from validated application settings."""

    return IngestionService(
        storage_directory=settings.data_dir,
        max_upload_size_bytes=settings.max_upload_size_mb * 1024 * 1024,
        registry=ParserRegistry(),
    )


def get_indexing_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> IndexingService:
    """Build the configured chunking, embedding, and vector storage pipeline."""

    return build_indexing_service(settings)


def get_structured_extraction_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> StructuredExtractionService:
    """Build deterministic CSV transaction extraction backed by SQLite."""

    return StructuredExtractionService(
        extractor=CsvTransactionExtractor(),
        repository=TransactionRepository(settings.database_path),
    )


@router.post("", response_model=IngestedDocument, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[UploadFile, File(description="A UTF-8 CSV or text-based PDF")],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
    indexing_service: Annotated[IndexingService, Depends(get_indexing_service)],
    extraction_service: Annotated[
        StructuredExtractionService, Depends(get_structured_extraction_service)
    ],
) -> IngestedDocument:
    """Validate, store, parse, chunk, embed, and index a financial document."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required.")

    try:
        content = await file.read(service.max_upload_size_bytes + 1)
        result = service.ingest(
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            content=content,
        )
        chunk_count = indexing_service.index(result)
        transaction_count = extraction_service.extract_and_store(result.document, content)
        return result.document.model_copy(
            update={"chunk_count": chunk_count, "transaction_count": transaction_count}
        )
    except UnsupportedDocumentError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except DocumentTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except InvalidDocumentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DocumentParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await file.close()
