"""
Vector Service — ChromaDB wrapper
Handles upsert, query, and delete of document chunks in the RAG knowledge base.
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

from app.services.embedding_service import generate_embeddings_batch, generate_embedding

_client: Optional[chromadb.Client] = None
_collection = None

COLLECTION_NAME = "alfalah_kb"


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.Client(
            Settings(is_persistent=True, persist_directory="./chroma_db")
        )
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


async def upsert_documents(
    ids: List[str],
    texts: List[str],
    metadatas: List[Dict[str, Any]],
) -> None:
    """
    Embeds and upserts a batch of text chunks into ChromaDB.
    ids       — Unique IDs per chunk (e.g. "prospectus_alfalah_ghp__chunk_0")
    texts     — The raw text chunks
    metadatas — Dicts with source info: {"source": "Alfalah GHP Prospectus", "doc_type": "prospectus", "fund_name": "..."}
    """
    collection = get_collection()
    embeddings = await generate_embeddings_batch(texts)
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )


async def search_documents(
    query: str,
    top_k: int = 5,
    where: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Semantic search across the knowledge base.
    Returns a list of {text, metadata, distance} dicts.
    `where` lets callers filter by metadata fields, e.g. {"fund_name": "Alfalah GHP Islamic Income Fund"}
    """
    collection = get_collection()
    query_embedding = await generate_embedding(query)

    kwargs: Dict[str, Any] = dict(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({"text": doc, "metadata": meta, "distance": dist})
    return output


async def delete_documents(ids: List[str]) -> None:
    """Deletes specific chunks by their IDs."""
    collection = get_collection()
    collection.delete(ids=ids)


async def delete_by_source(source_name: str) -> None:
    """Deletes all chunks belonging to a specific source document."""
    collection = get_collection()
    collection.delete(where={"source": source_name})
