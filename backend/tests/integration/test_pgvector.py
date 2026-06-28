"""Integration tests for the pgvector vector store backend.

These tests require a running PostgreSQL instance with the pgvector extension
and a valid DATABASE_URL. They are skipped unless the ``DATABASE_URL`` or
``PGVECTOR_TEST_DSN`` environment variable is set.

Example:
    docker run -d --name pgvector-test \
        -e POSTGRES_PASSWORD=postgres \
        -p 5432:5432 \
        pgvector/pgvector:pg16

    export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
    pytest tests/integration/test_pgvector.py -v
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.pgvector

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _get_dsn() -> str | None:
    return os.environ.get("PGVECTOR_TEST_DSN") or os.environ.get("DATABASE_URL")


@pytest.fixture(scope="module")
def pgvector_dsn() -> str:
    dsn = _get_dsn()
    if not dsn:
        pytest.skip("PGVECTOR_TEST_DSN or DATABASE_URL not set; skipping pgvector integration tests")
    return dsn


@pytest.fixture(autouse=True)
def _skip_without_dsn() -> None:
    if not _get_dsn():
        pytest.skip("pgvector not configured")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.pgvector
class TestPgVectorIntegration:
    @pytest.mark.asyncio
    async def test_upsert_search_delete(self, pgvector_dsn: str) -> None:
        from app.services.vector_store import PgVectorStore

        store = PgVectorStore(dsn=pgvector_dsn, table_name="test_vector_store", dimension=3)
        store.initialize()

        try:
            await store.upsert_documents(
                ids=["doc-1", "doc-2"],
                texts=["the cat sat on the mat", "dogs are loyal friends"],
                metadatas=[
                    {"source": "test.txt", "doc_type": "general"},
                    {"source": "test.txt", "doc_type": "general"},
                ],
                embeddings=[
                    [0.1, 0.2, 0.3],
                    [0.9, 0.8, 0.7],
                ],
            )

            results = await store.search_documents(
                query_embedding=[0.1, 0.2, 0.3], top_k=1
            )
            assert len(results) == 1
            assert results[0].text == "the cat sat on the mat"

            await store.delete_documents(["doc-1"])
            results = await store.search_documents(
                query_embedding=[0.1, 0.2, 0.3], top_k=5
            )
            assert len(results) == 1
            assert results[0].text == "dogs are loyal friends"
        finally:
            with store._get_pool().connection() as conn:
                conn.execute("DROP TABLE IF EXISTS test_vector_store")
                conn.commit()
            store.close()

    @pytest.mark.asyncio
    async def test_delete_by_source(self, pgvector_dsn: str) -> None:
        from app.services.vector_store import PgVectorStore

        store = PgVectorStore(dsn=pgvector_dsn, table_name="test_vector_store_src", dimension=3)
        store.initialize()

        try:
            await store.upsert_documents(
                ids=["a", "b"],
                texts=["alpha", "beta"],
                metadatas=[{"source": "src_a"}, {"source": "src_b"}],
                embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            )
            await store.delete_by_source("src_a")
            results = await store.search_documents(
                query_embedding=[0.1, 0.2, 0.3], top_k=5
            )
            assert len(results) == 1
            assert results[0].metadata["source"] == "src_b"
        finally:
            with store._get_pool().connection() as conn:
                conn.execute("DROP TABLE IF EXISTS test_vector_store_src")
                conn.commit()
            store.close()

    @pytest.mark.asyncio
    async def test_where_filter(self, pgvector_dsn: str) -> None:
        from app.services.vector_store import PgVectorStore

        store = PgVectorStore(dsn=pgvector_dsn, table_name="test_vector_store_wh", dimension=3)
        store.initialize()

        try:
            await store.upsert_documents(
                ids=["x", "y"],
                texts=["filtered", "other"],
                metadatas=[
                    {"source": "s", "fund_name": "Alfalah"},
                    {"source": "s", "fund_name": "Other"},
                ],
                embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            )
            results = await store.search_documents(
                query_embedding=[0.1, 0.2, 0.3],
                top_k=5,
                where={"fund_name": "Alfalah"},
            )
            assert len(results) == 1
            assert results[0].text == "filtered"
        finally:
            with store._get_pool().connection() as conn:
                conn.execute("DROP TABLE IF EXISTS test_vector_store_wh")
                conn.commit()
            store.close()
