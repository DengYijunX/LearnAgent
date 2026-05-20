import pytest

from app.tools.mock_learning_tools import (
    MockGitHubRepoAnalyzerTool,
    MockReadUrlTool,
    MockSearchWebTool,
)


@pytest.mark.asyncio
async def test_mock_search_web_tool_returns_query_summary():
    tool = MockSearchWebTool()

    result = await tool.call({"query": "LangGraph tutorial"}, context={})

    assert result.is_error is False
    assert "LangGraph tutorial" in result.content
    assert result.metadata["source"] == "mock"


@pytest.mark.asyncio
async def test_mock_read_url_tool_returns_url_summary():
    tool = MockReadUrlTool()

    result = await tool.call({"url": "https://example.com/docs"}, context={})

    assert result.is_error is False
    assert "https://example.com/docs" in result.content
    assert result.metadata["title"] == "Mock page"


@pytest.mark.asyncio
async def test_mock_github_repo_analyzer_returns_repo_summary():
    tool = MockGitHubRepoAnalyzerTool()

    result = await tool.call(
        {"repo_url": "https://github.com/huggingface/smolagents"},
        context={},
    )

    assert result.is_error is False
    assert "https://github.com/huggingface/smolagents" in result.content
    assert result.metadata["source"] == "mock"
