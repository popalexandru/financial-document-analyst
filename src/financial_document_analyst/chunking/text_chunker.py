"""Source-preserving text chunking."""

from hashlib import sha256

from financial_document_analyst.domain.documents import DocumentChunk, ParsedDocument


class InvalidChunkingConfigurationError(ValueError):
    """Raised when chunk size and overlap cannot guarantee forward progress."""


class TextChunker:
    """Split parsed segments into bounded overlapping chunks at natural boundaries."""

    def __init__(self, *, chunk_size: int, overlap: int) -> None:
        if chunk_size < 1:
            raise InvalidChunkingConfigurationError("Chunk size must be positive.")
        if overlap < 0 or overlap >= chunk_size:
            raise InvalidChunkingConfigurationError(
                "Chunk overlap must be non-negative and smaller than chunk size."
            )
        self._chunk_size = chunk_size
        self._overlap = overlap

    def chunk(self, document_id: str, parsed: ParsedDocument) -> list[DocumentChunk]:
        """Create deterministic chunks while retaining each segment's source location."""

        chunks: list[DocumentChunk] = []
        for segment in parsed.segments:
            for content in self._split_text(segment.content):
                chunk_index = len(chunks)
                chunk_id = sha256(
                    f"{document_id}:{segment.location}:{chunk_index}:{content}".encode()
                ).hexdigest()
                chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        document_id=document_id,
                        content=content,
                        location=segment.location,
                        chunk_index=chunk_index,
                        metadata={**segment.metadata, "source_location": segment.location},
                    )
                )
        return chunks

    def _split_text(self, text: str) -> list[str]:
        normalized = " ".join(text.split())
        if not normalized:
            return []

        parts: list[str] = []
        start = 0
        while start < len(normalized):
            tentative_end = min(start + self._chunk_size, len(normalized))
            end = self._natural_boundary(normalized, start, tentative_end)
            content = normalized[start:end].strip()
            if content:
                parts.append(content)
            if end == len(normalized):
                break
            start = max(end - self._overlap, start + 1)
        return parts

    def _natural_boundary(self, text: str, start: int, tentative_end: int) -> int:
        if tentative_end == len(text):
            return tentative_end

        earliest_break = start + int(self._chunk_size * 0.6)
        candidates = [
            text.rfind(separator, earliest_break, tentative_end)
            for separator in (". ", "; ", ", ", " ")
        ]
        boundary = max(candidates, default=-1)
        return boundary + 1 if boundary >= earliest_break else tentative_end
