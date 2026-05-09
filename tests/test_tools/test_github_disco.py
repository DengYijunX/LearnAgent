import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.tools.github_disco import search_github_repos, get_github_trending


@pytest.mark.asyncio
async def test_search_github_repos():
    mock_response = {"items": [
        {"full_name": "test/repo", "description": "测试仓库", "html_url": "https://github.com/test/repo", "stargazers_count": 100}
    ]}
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        results = await search_github_repos("langgraph")
        assert len(results) == 1
        assert results[0]["full_name"] == "test/repo"


@pytest.mark.asyncio
async def test_get_github_trending():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        results = await get_github_trending()
        assert isinstance(results, list)
