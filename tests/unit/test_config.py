"""Application configuration validation tests."""

import pytest
from pydantic import ValidationError

from financial_document_analyst.core.config import Settings


def test_settings_reject_overlap_equal_to_chunk_size() -> None:
    with pytest.raises(ValidationError, match="CHUNK_OVERLAP"):
        Settings(chunk_size=100, chunk_overlap=100)
