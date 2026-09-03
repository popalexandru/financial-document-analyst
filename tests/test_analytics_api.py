"""Analytics endpoint integration tests."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_upload_extracts_transactions_and_analytics_are_exact(test_app: FastAPI) -> None:
    transport = ASGITransport(app=test_app)
    content = (
        b"date,description,amount,currency,category\n"
        b"2026-07-02,Acme Telecom,-49.00,RON,utilities\n"
        b"2026-08-02,Acme Telecom,-49.00,RON,utilities\n"
        b"2026-08-03,Green Garden,-86.50,RON,restaurants\n"
        b"2026-08-08,Salary,7500.00,RON,income\n"
    )

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload = await client.post(
            "/documents", files={"file": ("statement.csv", content, "text/csv")}
        )
        summary = await client.get("/analytics/summary", params={"month": "2026-08"})
        categories = await client.get("/analytics/categories", params={"month": "2026-08"})
        merchant = await client.get("/analytics/merchants/Acme%20Telecom")
        recurring = await client.get("/analytics/recurring")

    assert upload.status_code == 201
    assert upload.json()["transaction_count"] == 4
    assert summary.json()["expense_cents"] == 13_550
    assert summary.json()["income_cents"] == 750_000
    assert categories.json()[0]["category"] == "restaurants"
    assert merchant.json()["amount_cents"] == 9800
    assert recurring.json()[0]["counterparty"] == "Acme Telecom"
