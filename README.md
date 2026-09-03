# Financial Document Analyst

Financial Document Analyst is a portfolio-grade API for extracting, searching, and
analyzing financial documents with retrieval-augmented generation and deterministic
calculation tools.

The project is being built incrementally. Milestone 0 provides the executable FastAPI
foundation, environment-based configuration, quality checks, and an automated health-check test.

## Requirements

- Python 3.11–3.13
- [`uv`](https://docs.astral.sh/uv/) (recommended)

## Local development

```bash
cp .env.example .env
uv sync --extra dev
uv run uvicorn financial_document_analyst.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the generated API documentation, or verify the service:

```bash
curl http://127.0.0.1:8000/health
```

## Quality checks

```bash
make check
```

## Current API

### `GET /health`

```json
{
  "status": "ok",
  "service": "Financial Document Analyst",
  "version": "0.1.0",
  "environment": "development"
}
```

## Roadmap

1. Document ingestion and parsing
2. Chunking, embeddings, and vector storage
3. RAG queries with source citations
4. Structured financial extraction and deterministic tools
5. Docker, reliability, and portfolio documentation

