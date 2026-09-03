"""Deterministic local embeddings for offline demos and tests."""

import hashlib
import math
import re


class LocalHashEmbeddingProvider:
    """Create normalized lexical vectors using a stable hashing trick.

    This provider has no model download or API cost. It is intentionally a demo baseline,
    not a replacement for semantic production embeddings.
    """

    def __init__(self, dimensions: int = 256) -> None:
        if dimensions < 1:
            raise ValueError("Embedding dimensions must be positive.")
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def name(self) -> str:
        return "local-hash"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Cannot embed empty text.")

        vector = [0.0] * self._dimensions
        for token in re.findall(r"\w+", text.casefold(), flags=re.UNICODE):
            digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
            value = int.from_bytes(digest, byteorder="big")
            index = value % self._dimensions
            sign = 1.0 if value & 1 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            raise ValueError("Text must contain at least one alphanumeric token.")
        return [value / norm for value in vector]
