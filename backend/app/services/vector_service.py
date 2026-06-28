"""
Vector Service — async facade over the configured vector store backend.

Public API is unchanged from the original ChromaDB-only implementation so that
callers (ingestion pipeline, search_kb tool, chroma admin router) require no
modifications. Backend selection is driven by `VECTOR_STORE_TYPE`.

Defaults:
  - chromadb  → in-process ChromaDB (existing behavior)
  - pgvector  → PostgreSQL + pgvector extension
"""

from typing import Any

from app.services.vector_store import SearchResult, get_vector_store


async def upsert_documents(
    ids: list[str],
    texts: list[str],
    metadatas: list[dict[str, Any]],
) -> None:
    """
    Embeds and upserts a batch of text chunks into the configured vector store.
    ids       — Unique IDs per chunk (e.g. "prospectus_alfalah_ghp__chunk_0")
    texts     — The raw text chunks
    metadatas — Dicts with source info, e.g. {"source": "...", "doc_type": "prospectus", "fund_name": "..."}
    """
    from app.services.embedding_service import generate_embeddings_batch

    store = get_vector_store()
    embeddings = await generate_embeddings_batch(texts)
    await store.upsert_documents(
        ids=ids, texts=texts, metadatas=metadatas, embeddings=embeddings
    )


async def search_documents(
    query: str,
    top_k: int = 5,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Semantic search across the knowledge base.
    Returns a list of {text, metadata, distance} dicts.
    `where` lets callers filter by metadata fields, e.g. {"fund_name": "Alfalah GHP Islamic Income Fund"}
    """
    from app.services.embedding_service import generate_embedding

    store = get_vector_store()
    query_embedding = await generate_embedding(query)
    results: list[SearchResult] = await store.search_documents(
        query_embedding=query_embedding, top_k=top_k, where=where
    )
    return [
        {"text": r.text, "metadata": r.metadata, "distance": r.distance}
        for r in results
    ]


async def delete_documents(ids: list[str]) -> None:
    """Deletes specific chunks by their IDs."""
    store = get_vector_store()
    await store.delete_documents(ids)


async def delete_by_source(source_name: str) -> None:
    """Deletes all chunks belonging to a specific source document."""
    store = get_vector_store()
    await store.delete_by_source(source_name)
