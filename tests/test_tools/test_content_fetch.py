import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.tools.content_fetch import fetch_content


@pytest.mark.asyncio
async def test_fetch_content_returns_markdown():
    mock_resp = MagicMock()
    mock_resp.text = "<html><body><article>RAG 简介</article></body></html>"
    mock_resp.raise_for_status = MagicMock()
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await fetch_content("https://example.com/rag")
        assert "RAG 简介" in result.content
        assert result.url == "https://example.com/rag"


@pytest.mark.asyncio
async def test_fetch_content_invalid_url():
    result = await fetch_content("")
    assert result.content == ""
    assert result.url == ""
