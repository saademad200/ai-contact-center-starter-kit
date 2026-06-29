"""
Vector Store Abstraction
========================
Protocol + adapters for pluggable vector store backends.

Backends:
  - ChromaDB  (default, in-process, persistent)
  - pgvector  (PostgreSQL + pgvector extension)

The public async API matches the legacy `vector_service` signatures so that
callers (ingestion pipeline, search_kb tool, chroma admin router) require no
changes when the default backend is selected.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from app.core.config import settings
from app.services.embedding_service import EMBEDDING_DIMENSION

log = logging.getLogger(__name__)


# ── Public result shape ──────────────────────────────────────────────────────


@dataclass(slots=True)
class SearchResult:
    """Single hit returned by `search_documents`."""

    text: str
    metadata: dict[str, Any]
    distance: float


# ── Protocol ──────────────────────────────────────────────────────────────────


@runtime_checkable
class VectorStore(Protocol):
    """Operational contract every vector store adapter must satisfy."""

    async def upsert_documents(
        self,
        ids: list[str],
        texts: list[str],
        metadatas: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None: ...

    async def search_documents(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[SearchResult]: ...

    async def delete_documents(self, ids: list[str]) -> None: ...

    async def delete_by_source(self, source: str) -> None: ...


# ── ChromaDB adapter ──────────────────────────────────────────────────────────


class ChromaVectorStore:
    """ChromaDB-backed vector store (default)."""

    def __init__(self, collection_name: str = "alfalah_kb") -> None:
        self._collection_name = collection_name
        self._client: Any = None
        self._collection: Any = None

    def _get_collection(self) -> Any:
        if self._collection is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self._client = chromadb.Client(
                ChromaSettings(is_persistent=True, persist_directory="./chroma_db")
            )
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    # -- public accessor used by the chroma admin router ------------------------
    def get_collection(self) -> Any:
        return self._get_collection()

    async def upsert_documents(
        self,
        ids: list[str],
        texts: list[str],
        metadatas: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        collection = self._get_collection()
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    async def search_documents(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        collection = self._get_collection()
        kwargs: dict[str, Any] = dict(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        if where:
            kwargs["where"] = where
        results = collection.query(**kwargs)
        output: list[SearchResult] = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
            strict=False,
        ):
            output.append(
                SearchResult(text=doc, metadata=meta, distance=float(dist))
            )
        return output

    async def delete_documents(self, ids: list[str]) -> None:
        collection = self._get_collection()
        collection.delete(ids=ids)

    async def delete_by_source(self, source: str) -> None:
        collection = self._get_collection()
        collection.delete(where={"source": source})


# ── pgvector adapter ─────────────────────────────────────────────────────────


class PgVectorStore:
    """PostgreSQL + pgvector backed vector store.

    Stores pre-generated embeddings from the embedding service.
    Uses cosine distance (`<=>`) to match ChromaDB's cosine semantics.

    Uses psycopg3's native AsyncConnectionPool for non-blocking I/O.
    """

    def __init__(
        self,
        dsn: str,
        table_name: str = "vector_store",
        dimension: int = EMBEDDING_DIMENSION,
    ) -> None:
        self._dsn = dsn
        self._table_name = table_name
        self._dimension = dimension
        self._pool: Any = None

    # -- connection pool lifecycle ----------------------------------------------

    async def _get_pool(self) -> Any:
        if self._pool is None:
            from psycopg_pool import AsyncConnectionPool

            self._pool = AsyncConnectionPool(
                conninfo=self._dsn,
                min_size=1,
                max_size=10,
                open=False,
            )
            await self._pool.open()
            log.info("[pgvector] async connection pool opened (table=%s)", self._table_name)
        return self._pool

    async def initialize(self) -> None:
        """Create extension, table, and indexes. Idempotent.

        Uses a sync connection for DDL since psycopg3's async pool
        doesn't support DDL transactions well. This runs once at startup.
        """
        import asyncio

        def _init_ddl() -> None:
            from psycopg import connect

            with connect(self._dsn) as conn:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self._table_name} (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        embedding vector({self._dimension}) NOT NULL,
                        source TEXT
                    );
                    """
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {self._table_name}_embedding_idx "
                    f"ON {self._table_name} USING hnsw (embedding vector_cosine_ops);"
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {self._table_name}_source_idx "
                    f"ON {self._table_name} (source);"
                )
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {self._table_name}_metadata_idx "
                    f"ON {self._table_name} USING GIN (metadata jsonb_path_ops);"
                )
                conn.commit()

        # DDL is sync-only; run in thread to avoid blocking the event loop
        await asyncio.to_thread(_init_ddl)
        log.info("[pgvector] schema initialized (table=%s)", self._table_name)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            log.info("[pgvector] connection pool closed")

    # -- helpers ---------------------------------------------------------------

    def _validate_embeddings(self, embeddings: list[list[float]]) -> None:
        for emb in embeddings:
            if len(emb) != self._dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self._dimension}, "
                    f"got {len(emb)}"
                )

    @staticmethod
    def _to_sql_where(where: dict[str, Any] | None) -> tuple[str, list[Any]]:
        """Convert a Chroma-style where dict into a parameterized SQL WHERE clause.

        Supports filtering by `source` (top-level column) and arbitrary
        metadata keys (JSONB lookup). This preserves ChromaDB's `where`
        semantics for the pgvector backend.
        """
        if not where:
            return "", []
        clauses: list[str] = []
        params: list[Any] = []
        for key, value in where.items():
            if key == "source":
                clauses.append("source = %s")
            else:
                clauses.append(f"metadata->>'{key}' = %s")
            params.append(value)
        where_sql = " AND ".join(clauses)
        return f"WHERE {where_sql}", params

    # -- VectorStore protocol --------------------------------------------------

    async def upsert_documents(
        self,
        ids: list[str],
        texts: list[str],
        metadatas: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        self._validate_embeddings(embeddings)
        upsert_sql = """
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                metadata = EXCLUDED.metadata,
                embedding = EXCLUDED.embedding,
                source = EXCLUDED.source
        """
        params: list[Any] = []
        values_placeholders: list[str] = []
        for _i, (doc_id, text, meta, emb) in enumerate(
            zip(ids, texts, metadatas, embeddings, strict=False)
        ):
            values_placeholders.append("(%s, %s, %s, %s, %s)")
            emb_literal = "[" + ",".join(str(v) for v in emb) + "]"
            params.extend([doc_id, text, meta, emb_literal, meta.get("source")])
        sql = (
            f"INSERT INTO {self._table_name} (id, content, metadata, embedding, source) "
            f"VALUES {', '.join(values_placeholders)} {upsert_sql}"
        )

        pool = await self._get_pool()
        async with pool.connection() as conn:
            await conn.execute(sql, params)
            await conn.commit()

    async def search_documents(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        where_clause, where_params = self._to_sql_where(where)
        emb_literal = "[" + ",".join(str(v) for v in query_embedding) + "]"
        sql = (
            f"SELECT content, metadata, (embedding <=> %s::vector) AS distance "
            f"FROM {self._table_name} {where_clause} "
            f"ORDER BY embedding <=> %s::vector ASC LIMIT %s"
        )
        params: list[Any] = [emb_literal, *where_params, emb_literal, top_k]

        pool = await self._get_pool()
        async with pool.connection() as conn:
            rows = (await conn.execute(sql, params)).fetchall()
        return [
            SearchResult(text=row[0], metadata=row[1], distance=float(row[2]))
            for row in rows
        ]

    async def delete_documents(self, ids: list[str]) -> None:
        if not ids:
            return
        placeholders = ", ".join(["%s"] * len(ids))
        sql = f"DELETE FROM {self._table_name} WHERE id IN ({placeholders})"

        pool = await self._get_pool()
        async with pool.connection() as conn:
            await conn.execute(sql, list(ids))
            await conn.commit()

    async def delete_by_source(self, source: str) -> None:
        sql = f"DELETE FROM {self._table_name} WHERE source = %s"

        pool = await self._get_pool()
        async with pool.connection() as conn:
            await conn.execute(sql, [source])
            await conn.commit()


# ── Factory ──────────────────────────────────────────────────────────────────


async def create_vector_store() -> VectorStore:
    """Build the configured vector store backend from settings."""
    backend = settings.vector_store_type.lower()
    if backend == "pgvector":
        if not settings.database_url:
            raise ValueError(
                "VECTOR_STORE_TYPE=pgvector requires DATABASE_URL to be set"
            )
        pg_store = PgVectorStore(
            dsn=settings.database_url,
            dimension=settings.pgvector_dimension,
        )
        await pg_store.initialize()
        log.info("[vector_store] using pgvector backend")
        return pg_store
    if backend == "chromadb":
        chroma_store = ChromaVectorStore()
        log.info("[vector_store] using ChromaDB backend")
        return chroma_store
    raise ValueError(
        f"Unknown VECTOR_STORE_TYPE={settings.vector_store_type!r}; "
        f"expected 'chromadb' or 'pgvector'"
    )


# ── Singleton ────────────────────────────────────────────────────────────────-

_store: VectorStore | None = None


async def get_vector_store_async() -> VectorStore:
    """Initialise (if needed) and return the configured vector store."""
    global _store
    if _store is None:
        _store = await create_vector_store()
    return _store


def get_vector_store() -> VectorStore:
    """Return the already-initialised vector store (fails if not ready)."""
    if _store is None:
        raise RuntimeError(
            "Vector store not initialised. Call get_vector_store_async() first."
        )
    return _store


async def reset_vector_store() -> None:
    """Reset the singleton (used by tests and shutdown)."""
    global _store
    if isinstance(_store, PgVectorStore):
        await _store.close()
    _store = None
