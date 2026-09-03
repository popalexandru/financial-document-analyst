"""Document upload API tests."""

from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_upload_csv_returns_ingestion_metadata(test_app: FastAPI) -> None:
    transport = ASGITransport(app=test_app)
    content = b"date,description,amount\n2026-08-01,Coffee,-12.50\n"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/documents", files={"file": ("statement.csv", content, "text/csv")}
        )

    payload = response.json()
    assert response.status_code == 201
    assert payload["original_filename"] == "statement.csv"
    assert payload["document_type"] == "csv"
    assert payload["segment_count"] == 1
    assert payload["size_bytes"] == len(content)
    assert len(payload["sha256"]) == 64
    assert Path(payload["stored_filename"]).suffix == ".csv"


@pytest.mark.anyio
async def test_upload_rejects_unsupported_extension(test_app: FastAPI) -> None:
    transport = ASGITransport(app=test_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/documents", files={"file": ("notes.txt", b"hello", "text/plain")}
        )

    assert response.status_code == 415
    assert response.json() == {"detail": "Only PDF and CSV documents are supported."}


@pytest.mark.anyio
async def test_upload_rejects_empty_document(test_app: FastAPI) -> None:
    transport = ASGITransport(app=test_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/documents", files={"file": ("empty.csv", b"", "text/csv")})

    assert response.status_code == 400
    assert response.json() == {"detail": "Uploaded document is empty."}


@pytest.mark.anyio
async def test_upload_rejects_document_above_configured_limit(test_app: FastAPI) -> None:
    transport = ASGITransport(app=test_app)
    oversized_content = b"x" * (10 * 1024 * 1024 + 1)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/documents",
            files={"file": ("oversized.csv", oversized_content, "text/csv")},
        )

    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"]


@pytest.mark.anyio
async def test_upload_rejects_unparseable_document(test_app: FastAPI) -> None:
    transport = ASGITransport(app=test_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/documents", files={"file": ("invalid.pdf", b"not a pdf", "application/pdf")}
        )

    assert response.status_code == 422
    assert response.json() == {"detail": "PDF structure could not be parsed."}
