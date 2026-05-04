"""
PDF Ingestion Pipeline
Reads PDFs from a local directory (or S3), parses them, chunks them,
and upserts chunks into ChromaDB via vector_service.
"""

import asyncio
import hashlib
import re
from pathlib import Path
from typing import Any

import pdfplumber  # pip install pdfplumber

from app.services.vector_service import upsert_documents

CHUNK_SIZE = 600  # characters per chunk (approx 150 tokens)
CHUNK_OVERLAP = 100  # overlap so context isn't cut abruptly


def _clean_text(text: str) -> str:
    """Remove boilerplate and normalize whitespace."""
    # Strip page numbers (e.g. "Page 1 of 20")
    text = re.sub(r"Page\s+\d+\s+of\s+\d+", "", text, flags=re.IGNORECASE)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _chunk_text(
    text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """Simple character-level sliding window chunker."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if len(c.strip()) > 50]


def _make_id(source: str, chunk_idx: int) -> str:
    """Deterministic chunk ID based on source name and chunk index."""
    base = f"{source}__chunk_{chunk_idx}"
    return hashlib.md5(base.encode()).hexdigest()


async def ingest_pdf(
    pdf_path: str,
    fund_name: str | None = None,
    doc_type: str = "general",
) -> int:
    """
    Parses a single PDF, chunks it, and upserts into ChromaDB.
    Returns the number of chunks ingested.
    """
    source_name = Path(pdf_path).stem

    with pdfplumber.open(pdf_path) as pdf:
        raw_pages = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                raw_pages.append(text)

    full_text = _clean_text(" ".join(raw_pages))
    chunks = _chunk_text(full_text)

    if not chunks:
        print(f"[Ingest] No content extracted from {pdf_path}")
        return 0

    ids = [_make_id(source_name, i) for i in range(len(chunks))]
    metadatas: list[dict[str, Any]] = [
        {
            "source": source_name,
            "doc_type": doc_type,
            "fund_name": fund_name or "general",
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]

    await upsert_documents(ids=ids, texts=chunks, metadatas=metadatas)
    print(f"[Ingest] {source_name} → {len(chunks)} chunks upserted.")
    return len(chunks)


async def ingest_directory(directory: str = "knowledge_base/docs") -> None:
    """Ingests all PDFs found in the given directory."""
    pdf_paths = list(Path(directory).glob("**/*.pdf"))
    if not pdf_paths:
        print(f"[Ingest] No PDFs found in {directory}")
        return
    for pdf_path in pdf_paths:
        await ingest_pdf(str(pdf_path))


if __name__ == "__main__":
    asyncio.run(ingest_directory())
