"""
Shared test fixtures.
"""

import sys
from unittest.mock import MagicMock

# Stub sentence_transformers before any app imports to avoid the broken
# transformers → keras v3 dependency chain in the local environment.
_mock_st = MagicMock()
_mock_st.SentenceTransformer = MagicMock
sys.modules.setdefault("sentence_transformers", _mock_st)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.dependencies import require_admin  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    """TestClient with admin auth bypassed via dependency override."""
    app.dependency_overrides[require_admin] = lambda: {"sub": "testadmin", "role": "admin"}
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def make_table():
    """
    Factory fixture that returns a pre-configured DynamoDB Table MagicMock.

    Usage:
        table = make_table(scan={"Items": [...]}, get_item={"Item": {...}})
    """

    def _factory(
        get_item: dict | None = None,
        scan: dict | None = None,
        query: dict | None = None,
    ) -> MagicMock:
        table = MagicMock()
        table.put_item.return_value = {}
        table.update_item.return_value = {}
        table.delete_item.return_value = {}
        table.get_item.return_value = get_item if get_item is not None else {}
        table.scan.return_value = scan if scan is not None else {"Items": []}
        table.query.return_value = query if query is not None else {"Items": []}
        return table

    return _factory
