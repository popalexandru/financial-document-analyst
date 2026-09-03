# Financial Document Analyst

Financial Document Analyst is a portfolio-grade API for extracting, searching, and
analyzing financial documents with retrieval-augmented generation and deterministic
calculation tools.

The project is being built incrementally. It currently provides an executable FastAPI foundation,
environment-based configuration, PDF/CSV ingestion, source-addressable parsing, quality checks,
local or OpenAI embeddings, persistent Chroma vector indexing, and automated tests.

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

### `POST /documents`

Uploads, validates, stores, and parses a UTF-8 CSV or text-based PDF. The default upload limit is
10 MB and can be changed through `MAX_UPLOAD_SIZE_MB`.

```bash
curl -X POST http://127.0.0.1:8000/documents \
  -F "file=@sample_data/transactions.csv;type=text/csv"
```

Example response:

```json
{
  "id": "8fcd148f-f66a-44c5-b708-77395154c768",
  "original_filename": "transactions.csv",
  "document_type": "csv",
  "content_type": "text/csv",
  "size_bytes": 327,
  "sha256": "<sha256 checksum>",
  "segment_count": 5,
  "stored_filename": "8fcd148f-f66a-44c5-b708-77395154c768.csv",
  "created_at": "2026-09-03T12:00:00Z"
}
```

CSV rows retain their source row number and PDF text retains its page number. Scanned PDFs are
rejected clearly because OCR is outside the current MVP.

## Vector indexing

Every parsed source segment is split into bounded chunks with overlap. Each chunk retains its
document ID and original page or row, receives an embedding, and is upserted into a persistent
Chroma collection under `data/chroma`.

The default `EMBEDDING_PROVIDER=local` uses deterministic lexical hashing. It requires no account,
model download, network connection, or API cost, making the repository testable at any time. It is
an offline demo baseline rather than a production-quality semantic model.

To use OpenAI embeddings instead:

```env
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=256
```

Provider/model combinations use separate Chroma collections so incompatible vector spaces cannot
be mixed. The OpenAI adapter batches document inputs, following the official embeddings API.

## RAG queries with citations

Ask a question after uploading at least one document:

```bash
curl -X POST http://127.0.0.1:8000/queries \
  -H "Content-Type: application/json" \
  -d '{"question":"restaurant","top_k":2,"minimum_score":0.05}'
```

The query is embedded with the same provider used for indexing. Chroma returns the closest chunks,
the configured generator creates the answer, and the application attaches trusted citations from
stored metadata. Citations contain the document ID, original filename, source page or row, chunk
ID, similarity score, and excerpt.

`GENERATION_PROVIDER=local` returns ranked source text and keeps the demo fully offline. Set it to
`openai` to synthesize a natural-language answer through the Responses API. OpenAI requests use
`store=False`; enabling the provider still sends the retrieved financial context to OpenAI.

## Roadmap

1. Chunking, embeddings, and vector storage
2. RAG queries with source citations
3. Structured financial extraction and deterministic tools
4. Docker, reliability, and portfolio documentation
