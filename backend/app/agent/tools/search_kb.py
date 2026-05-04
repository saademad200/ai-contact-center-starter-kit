from app.services.vector_service import search_documents


async def search_kb(query: str, fund_name: str | None = None) -> str:
    """
    Queries the RAG ChromaDB knowledge base to answer policy or document-based questions.
    Optionally filter by fund name to get more precise results.
    """
    try:
        where_filter = {"fund_name": fund_name} if fund_name else None
        results = await search_documents(query=query, top_k=3, where=where_filter)

        if not results:
            return "No relevant information found in the knowledge base."

        parts = []
        for r in results:
            source = r["metadata"].get("source", "Unknown")
            parts.append(f"[Source: {source}]\n{r['text']}")

        return "\n\n---\n\n".join(parts)

    except Exception as e:
        return f"Error querying knowledge base: {str(e)}"
