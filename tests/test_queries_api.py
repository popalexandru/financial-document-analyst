"""End-to-end query API tests over temporary persistent Chroma storage."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_query_returns_indexed_evidence_with_citations(test_app: FastAPI) -> None:
    transport = ASGITransport(app=test_app)
    content = (
        b"date,description,amount,currency\n"
        b"2026-08-01,Coffee Shop,-12.50,RON\n"
        b"2026-08-02,Salary,7500.00,RON\n"
    )

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_response = await client.post(
            "/documents", files={"file": ("statement.csv", content, "text/csv")}
        )
        document_id = upload_response.json()["id"]
        query_response = await client.post(
            "/queries",
            json={
                "question": "Coffee",
                "document_id": document_id,
                "top_k": 1,
                "minimum_score": 0.01,
            },
        )

    payload = query_response.json()
    assert upload_response.status_code == 201
    assert query_response.status_code == 200
    assert payload["generator"] == "local-extractive"
    assert payload["retrieved_count"] == 1
    assert payload["citations"][0]["document_id"] == document_id
    assert payload["citations"][0]["filename"] == "statement.csv"
    assert payload["citations"][0]["location"] == "row 2"
    assert "Coffee Shop" in payload["answer"]


@pytest.mark.anyio
async def test_query_returns_safe_empty_answer_for_empty_index(test_app: FastAPI) -> None:
    transport = ASGITransport(app=test_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/queries", json={"question": "restaurants"})

    assert response.status_code == 200
    assert response.json()["citations"] == []
    assert response.json()["retrieved_count"] == 0


@pytest.mark.anyio
async def test_query_validates_question_and_top_k(test_app: FastAPI) -> None:
    transport = ASGITransport(app=test_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/queries", json={"question": "x", "top_k": 21})

    assert response.status_code == 422
