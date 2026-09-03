.PHONY: install run test lint format typecheck check

install:
	uv sync --extra dev

run:
	uv run uvicorn financial_document_analyst.main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy

check: lint typecheck test

