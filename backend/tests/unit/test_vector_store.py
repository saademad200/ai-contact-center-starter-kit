"""Unit tests for vector store abstraction and adapter selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class FakeResult:
    text: str
    metadata: dict[str, Any]
    distance: float


class FakeChromaCollection:
    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}
        self._meta: dict[str, Any] = {"hnsw:space": "cosine"}
        self._name = "alfalah_kb"
        self.deleted: list[list[str]] = []
        self.deleted_where: list[dict[str, Any]] = []

    def count(self) -> int:
        return len(self._rows)

    @property
    def name(self) -> str:
        return self._name

    @property
    def metadata(self) -> dict[str, Any]:
        return self._meta

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        for i, doc_id in enumerate(ids):
            self._rows[doc_id] = {
                "embedding": embeddings[i],
                "document": documents[i],
                "metadata": metadatas[i],
            }

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int = 5,
        include: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> dict[str, list[list[Any]]]:
        docs: list[str] = []
        metas: list[dict[str, Any]] = []
        dists: list[float] = []
        rows = list(self._rows.values())
        if where:
            key, value = next(iter(where.items()))
            rows = [r for r in rows if r["metadata"].get(key) == value]
        for r in rows[:n_results]:
            docs.append(r["document"])
            metas.append(r["metadata"])
            dists.append(0.0)
        return {"documents": [docs], "metadatas": [metas], "distances": [dists]}

    def get(self, **kwargs: Any) -> dict[str, list[Any]]:
        ids = list(self._rows.keys())
        docs = [self._rows[i]["document"] for i in ids]
        metas = [self._rows[i]["metadata"] for i in ids]
        return {"ids": ids, "documents": docs, "metadatas": metas}

    def delete(self, ids: list[str] | None = None, where: dict[str, Any] | None = None) -> None:
        if ids is not None:
            self.deleted.append(ids)
            for i in ids:
                self._rows.pop(i, None)
        elif where is not None:
            self.deleted_where.append(where)
            key, value = next(iter(where.items()))
            to_delete = [k for k, v in self._rows.items() if v["metadata"].get(key) == value]
            for k in to_delete:
                del self._rows[k]


# ---------------------------------------------------------------------------
# Tests: factory / adapter selection
# ---------------------------------------------------------------------------


class TestFactory:
    def test_default_is_chromadb(self) -> None:
        from app.core.config import settings
        from app.services.vector_store import ChromaVectorStore, create_vector_store

        assert settings.vector_store_type == "chromadb"
        # For chromadb, create_vector_store returns synchronously
        import asyncio

        store = asyncio.run(create_vector_store())
        assert isinstance(store, ChromaVectorStore)

    def test_pgvector_requires_database_url(self) -> None:
        from app.services.vector_store import create_vector_store

        with patch("app.services.vector_store.settings") as s:
            s.vector_store_type = "pgvector"
            s.database_url = ""
            with pytest.raises(ValueError, match="DATABASE_URL"):
                import asyncio

                asyncio.run(create_vector_store())

    def test_unknown_backend_raises(self) -> None:
        from app.services.vector_store import create_vector_store

        with patch("app.services.vector_store.settings") as s:
            s.vector_store_type = "pinecone"
            s.database_url = "postgresql://x"
            with pytest.raises(ValueError, match="Unknown VECTOR_STORE_TYPE"):
                import asyncio

                asyncio.run(create_vector_store())


# ---------------------------------------------------------------------------
# Tests: ChromaDB adapter preserves existing behavior
# ---------------------------------------------------------------------------


class TestChromaAdapter:
    @pytest.mark.asyncio
    async def test_upsert_then_search(self) -> None:
        from app.services.vector_store import ChromaVectorStore

        store = ChromaVectorStore.__new__(ChromaVectorStore)
        store._collection_name = "alfalah_kb"
        store._client = None
        store._collection = FakeChromaCollection()

        await store.upsert_documents(
            ids=["id1", "id2"],
            texts=["hello world", "foo bar"],
            metadatas=[{"source": "a"}, {"source": "b"}],
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
        )
        results = await store.search_documents(query_embedding=[0.1, 0.2], top_k=5)
        assert len(results) == 2
        assert results[0].text == "hello world"
        assert results[0].metadata["source"] == "a"

    @pytest.mark.asyncio
    async def test_search_with_where(self) -> None:
        from app.services.vector_store import ChromaVectorStore

        store = ChromaVectorStore.__new__(ChromaVectorStore)
        store._collection_name = "alfalah_kb"
        store._client = None
        store._collection = FakeChromaCollection()

        await store.upsert_documents(
            ids=["id1", "id2"],
            texts=["a", "b"],
            metadatas=[{"source": "x"}, {"source": "y"}],
            embeddings=[[0.1], [0.2]],
        )
        results = await store.search_documents(
            query_embedding=[0.1], top_k=5, where={"source": "y"}
        )
        assert len(results) == 1
        assert results[0].metadata["source"] == "y"

    @pytest.mark.asyncio
    async def test_delete_documents(self) -> None:
        from app.services.vector_store import ChromaVectorStore

        store = ChromaVectorStore.__new__(ChromaVectorStore)
        store._collection_name = "alfalah_kb"
        store._client = None
        store._collection = FakeChromaCollection()

        await store.upsert_documents(
            ids=["id1", "id2"],
            texts=["a", "b"],
            metadatas=[{"source": "x"}, {"source": "y"}],
            embeddings=[[0.1], [0.2]],
        )
        await store.delete_documents(["id1"])
        assert store._collection.deleted == [["id1"]]

    @pytest.mark.asyncio
    async def test_delete_by_source(self) -> None:
        from app.services.vector_store import ChromaVectorStore

        store = ChromaVectorStore.__new__(ChromaVectorStore)
        store._collection_name = "alfalah_kb"
        store._client = None
        store._collection = FakeChromaCollection()

        await store.upsert_documents(
            ids=["id1", "id2"],
            texts=["a", "b"],
            metadatas=[{"source": "x"}, {"source": "y"}],
            embeddings=[[0.1], [0.2]],
        )
        await store.delete_by_source("y")
        assert store._collection.deleted_where == [{"source": "y"}]


# ---------------------------------------------------------------------------
# Tests: pgvector adapter (mocked psycopg)
# ---------------------------------------------------------------------------


class TestPgVectorStore:
    @staticmethod
    def _make_async_pool_mock() -> tuple[Any, Any]:
        """Create a mock async pool + connection for testing."""
        from unittest.mock import AsyncMock

        pool = MagicMock()
        conn = AsyncMock()

        # Build an async context manager mock
        async_cm = MagicMock()
        async_cm.__aenter__ = AsyncMock(return_value=conn)
        async_cm.__aexit__ = AsyncMock(return_value=False)
        pool.connection.return_value = async_cm
        return pool, conn

    @pytest.mark.asyncio
    async def test_upsert_then_search(self) -> None:
        from app.services.vector_store import PgVectorStore

        pool, conn = self._make_async_pool_mock()

        store = PgVectorStore(dsn="postgresql://x", dimension=3)
        store._pool = pool

        await store.upsert_documents(
            ids=["id1"],
            texts=["hello"],
            metadatas=[{"source": "a"}],
            embeddings=[[0.1, 0.2, 0.3]],
        )
        assert conn.execute.called

        # For search: conn.execute is AsyncMock, so we need to mock the
        # result of `await conn.execute(...)` to have a .fetchall() method
        fake_result = MagicMock()
        fake_result.fetchall.return_value = [("hello", {"source": "a"}, 0.05)]
        conn.execute.return_value = fake_result
        results = await store.search_documents(query_embedding=[0.1, 0.2, 0.3], top_k=1)
        assert len(results) == 1
        assert results[0].text == "hello"
        assert results[0].distance == 0.05

    @pytest.mark.asyncio
    async def test_dimension_mismatch_raises(self) -> None:
        from app.services.vector_store import PgVectorStore

        store = PgVectorStore(dsn="postgresql://x", dimension=3)
        with pytest.raises(ValueError, match="dimension mismatch"):
            await store.upsert_documents(
                ids=["id1"],
                texts=["x"],
                metadatas=[{}],
                embeddings=[[0.1, 0.2]],  # wrong dim
            )

    @pytest.mark.asyncio
    async def test_delete_by_source(self) -> None:
        from app.services.vector_store import PgVectorStore

        pool, conn = self._make_async_pool_mock()

        store = PgVectorStore(dsn="postgresql://x", dimension=3)
        store._pool = pool
        await store.delete_by_source("doc_a")
        args, _ = conn.execute.call_args
        assert "source" in args[0]
        assert "doc_a" in args[1]

    @pytest.mark.asyncio
    async def test_initialize_runs_schema_sql(self) -> None:
        from unittest.mock import patch

        from app.services.vector_store import PgVectorStore

        fake_conn = MagicMock()
        fake_conn.__enter__ = MagicMock(return_value=fake_conn)
        fake_conn.__exit__ = MagicMock(return_value=False)
        store = PgVectorStore(dsn="postgresql://x", dimension=3)

        with patch("psycopg.connect", return_value=fake_conn) as mock_connect:
            await store.initialize()
            assert mock_connect.called
        assert fake_conn.execute.call_count >= 4
        assert fake_conn.commit.called
