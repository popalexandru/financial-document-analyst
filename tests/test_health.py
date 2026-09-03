"""Health endpoint tests."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_health_check_returns_service_metadata(test_app: FastAPI) -> None:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Financial Document Analyst",
        "version": "0.1.0",
        "environment": "test",
    }
