import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.tools.web_search import web_search


@pytest.mark.asyncio
async def test_web_search_returns_results():
    mock_response = {
        "results": [
            {"title": "RAG 入门", "url": "https://example.com/rag", "content": "RAG 是检索增强生成..."}
        ]
    }
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp
        results = await web_search("什么是 RAG")
        assert len(results) == 1
        assert results[0]["title"] == "RAG 入门"


@pytest.mark.asyncio
async def test_web_search_empty_query_returns_empty():
    results = await web_search("")
    assert results == []
