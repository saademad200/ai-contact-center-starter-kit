"""
Unit tests for AI Agent tools and pipeline components.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────
# Tests: tool_registry
# ─────────────────────────────────────────────────────────────
class TestToolRegistry:
    def test_all_tools_registered(self) -> None:
        from app.agent.tool_registry import OPENAI_TOOLS, TOOL_FUNCTIONS

        assert "get_fund_nav" in TOOL_FUNCTIONS
        assert "get_fund_performance" in TOOL_FUNCTIONS
        assert "search_kb" in TOOL_FUNCTIONS
        assert len(OPENAI_TOOLS) == 3

    def test_openai_tools_schema_valid(self) -> None:
        from app.agent.tool_registry import OPENAI_TOOLS

        for tool in OPENAI_TOOLS:
            assert tool["type"] == "function"
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]

    @pytest.mark.asyncio
    async def test_execute_tool_unknown(self) -> None:
        from app.agent.tool_registry import execute_tool

        result = await execute_tool("nonexistent_tool", "{}")
        assert "not registered" in result

    @pytest.mark.asyncio
    async def test_execute_tool_get_fund_nav(self) -> None:
        import json

        from app.agent.tool_registry import execute_tool

        args = json.dumps({"fund_name": "Alfalah GHP Income Fund"})
        with patch("app.agent.tools.get_fund_nav.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.text = "<html><body>NAV data</body></html>"
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value.get = AsyncMock(return_value=mock_response)
            result = await execute_tool("get_fund_nav", args)
            assert "Alfalah GHP Income Fund" in result


# ─────────────────────────────────────────────────────────────
# Tests: embedding_service
# ─────────────────────────────────────────────────────────────
class TestEmbeddingService:
    @pytest.mark.asyncio
    async def test_generate_embedding_returns_list(self) -> None:
        from app.services.embedding_service import generate_embedding

        embedding = await generate_embedding("test query about mutual funds")
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # all-MiniLM-L6-v2 output dim

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self) -> None:
        from app.services.embedding_service import generate_embeddings_batch

        texts = ["fund one", "fund two", "policy text"]
        embeddings = await generate_embeddings_batch(texts)
        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)


# ─────────────────────────────────────────────────────────────
# Tests: ingestion pipeline
# ─────────────────────────────────────────────────────────────
class TestIngestionPipeline:
    def test_clean_text(self) -> None:
        from app.pipeline.ingestion import _clean_text

        raw = "  Hello   World Page 1 of 20  "
        cleaned = _clean_text(raw)
        assert "Page 1 of 20" not in cleaned
        assert cleaned == "Hello World"

    def test_chunk_text(self) -> None:
        from app.pipeline.ingestion import _chunk_text

        long_text = "A" * 2000
        chunks = _chunk_text(long_text, chunk_size=600, overlap=100)
        assert len(chunks) > 1
        # Each chunk should not exceed chunk_size
        assert all(len(c) <= 600 for c in chunks)

    def test_make_id_deterministic(self) -> None:
        from app.pipeline.ingestion import _make_id

        id1 = _make_id("prospectus_alfalah", 0)
        id2 = _make_id("prospectus_alfalah", 0)
        assert id1 == id2
        assert _make_id("prospectus_alfalah", 0) != _make_id("prospectus_alfalah", 1)
