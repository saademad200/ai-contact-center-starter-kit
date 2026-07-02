"""
Chroma Router — admin visibility into the ChromaDB vector store
================================================================
GET  /api/v1/chroma/stats              — collection stats (count, metadata)
GET  /api/v1/chroma/documents          — paginated list of stored chunks
GET  /api/v1/chroma/search?q=<query>   — run a semantic search (for debugging)
DELETE /api/v1/chroma/documents/{id}   — delete a single chunk by ID

NOTE: These endpoints are ChromaDB-specific and return HTTP 501 when
      VECTOR_STORE_TYPE=pgvector is configured.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import require_admin
from app.services.vector_service import (
    delete_documents,
    search_documents,
)
from app.services.vector_store import ChromaVectorStore, get_vector_store

router = APIRouter(prefix="/chroma", tags=["chroma"])


# ── Helpers ───────────────────────────────────────────────────────────────────


def _require_chroma() -> ChromaVectorStore:
    """Return the ChromaVectorStore, or raise 501 if another backend is active."""
    store = get_vector_store()
    if not isinstance(store, ChromaVectorStore):
        raise HTTPException(
            status_code=501,
            detail=(
                "ChromaDB admin endpoints are not available when "
                "VECTOR_STORE_TYPE=pgvector. Use your PostgreSQL tooling to "
                "inspect the vector_store table directly."
            ),
        )
    return store


def _collection_info(store: ChromaVectorStore) -> dict[str, Any]:
    """Return raw collection metadata from ChromaDB."""
    col = store.get_collection()
    return {
        "name": col.name,
        "count": col.count(),
        "metadata": col.metadata or {},
    }


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("/stats")
def chroma_stats(
    _: Annotated[str, Depends(require_admin)],
) -> dict[str, Any]:
    """
    Returns high-level stats for the alfalah_kb collection:
    - Total chunk count
    - Collection name and HNSW metadata
    - Breakdown of unique source documents stored
    """
    store = _require_chroma()
    col = store.get_collection()
    info = _collection_info(store)

    # Get all stored metadatas to compute per-source breakdown
    try:
        results = col.get(include=["metadatas"])
        metadatas = results.get("metadatas") or []
        source_counts: dict[str, int] = {}
        for meta in metadatas:
            src = (meta or {}).get("source", "unknown")
            source_counts[src] = source_counts.get(src, 0) + 1
    except Exception:
        source_counts = {}

    return {
        "collection": info,
        "sources": [
            {"source": src, "chunks": count}
            for src, count in sorted(source_counts.items())
        ],
        "total_sources": len(source_counts),
    }


@router.get("/documents")
def chroma_list_documents(
    _: Annotated[str, Depends(require_admin)],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    source: str | None = Query(default=None, description="Filter by source filename"),
) -> dict[str, Any]:
    """
    Returns a paginated list of raw chunks stored in ChromaDB.
    Optionally filter by source document name.
    """
    store = _require_chroma()
    col = store.get_collection()

    try:
        kwargs: dict[str, Any] = {
            "include": ["documents", "metadatas"],
            "offset": offset,
            "limit": limit,
        }
        if source:
            kwargs["where"] = {"source": source}

        results = col.get(**kwargs)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    ids = results.get("ids") or []
    docs = results.get("documents") or []
    metas = results.get("metadatas") or []

    items = [
        {
            "id": chunk_id,
            "text": text[:300] + ("…" if len(text) > 300 else ""),
            "metadata": meta,
        }
        for chunk_id, text, meta in zip(ids, docs, metas, strict=False)
    ]

    return {
        "offset": offset,
        "limit": limit,
        "returned": len(items),
        "items": items,
    }


@router.get("/search")
async def chroma_search(
    _: Annotated[str, Depends(require_admin)],
    q: str = Query(..., min_length=1, description="Search query"),
    top_k: int = Query(default=5, ge=1, le=20),
) -> dict[str, Any]:
    """
    Runs a semantic search against the knowledge base.
    Useful for verifying that uploaded documents are being retrieved correctly.
    """
    _require_chroma()  # guard — raises 501 if pgvector is active

    try:
        results = await search_documents(query=q, top_k=top_k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "query": q,
        "top_k": top_k,
        "results": [
            {
                "text": r["text"][:400] + ("…" if len(r["text"]) > 400 else ""),
                "metadata": r["metadata"],
                "distance": round(r["distance"], 4),
            }
            for r in results
        ],
    }


@router.delete("/documents/{chunk_id}")
async def chroma_delete_chunk(
    chunk_id: str,
    _: Annotated[str, Depends(require_admin)],
) -> dict[str, str]:
    """
    Deletes a single chunk from ChromaDB by its ID.
    Use with caution — this bypasses the DynamoDB document record.
    """
    _require_chroma()  # guard — raises 501 if pgvector is active

    try:
        await delete_documents([chunk_id])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"deleted": chunk_id}
