"""Environment-based application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, PositiveInt, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated settings loaded from environment variables or a local `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Financial Document Analyst"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    data_dir: Path = Path("data/documents")
    max_upload_size_mb: PositiveInt = 10
    chroma_dir: Path = Path("data/chroma")
    database_path: Path = Path("data/financial.db")
    chunk_size: PositiveInt = 800
    chunk_overlap: int = Field(default=120, ge=0)
    embedding_provider: Literal["local", "openai"] = "local"
    embedding_dimensions: PositiveInt = 256
    openai_embedding_model: str = "text-embedding-3-small"
    generation_provider: Literal["local", "openai"] = "local"
    openai_generation_model: str = "gpt-5.4-mini"
    rag_top_k: PositiveInt = 5
    rag_minimum_score: float = Field(default=0.05, ge=0.0, le=1.0)
    openai_api_key: str | None = Field(default=None, repr=False)

    @model_validator(mode="after")
    def validate_chunking_settings(self) -> Self:
        """Ensure overlap cannot prevent the chunker from advancing."""

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return one immutable-by-convention settings instance per process."""

    return Settings()
