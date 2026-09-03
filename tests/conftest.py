"""Shared pytest fixtures."""

from pathlib import Path

import pytest
from fastapi import FastAPI

from financial_document_analyst.core.config import Settings, get_settings
from financial_document_analyst.main import create_app


@pytest.fixture
def anyio_backend() -> str:
    """Run async tests on the asyncio backend used by the application."""

    return "asyncio"


@pytest.fixture
def test_app(tmp_path: Path) -> FastAPI:
    """Provide an isolated application with deterministic test settings."""

    settings = Settings(app_env="test", data_dir=tmp_path / "documents")
    application = create_app(settings)
    application.dependency_overrides[get_settings] = lambda: settings

    return application
