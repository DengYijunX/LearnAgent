"""Tests for GitHub repo analyzer tool."""

import os

import pytest


class TestMockGitHubAnalyzer:
    @pytest.mark.asyncio
    async def test_mock_analyzes_repo_url(self):
        from app.tools.github_analyzer import MockGitHubAnalyzer

        tool = MockGitHubAnalyzer()
        result = await tool.call({"repo_url": "https://github.com/huggingface/smolagents"})
        assert result.get("isError") is False
        assert "content" in result
        assert "smolagents" in str(result["content"])

    @pytest.mark.asyncio
    async def test_mock_extracts_owner_repo(self):
        from app.tools.github_analyzer import MockGitHubAnalyzer

        tool = MockGitHubAnalyzer()
        result = await tool.call({"repo_url": "https://github.com/langchain-ai/langgraph"})
        assert "langchain-ai" in str(result).lower() or "langgraph" in str(result).lower()

    @pytest.mark.asyncio
    async def test_mock_returns_readme_and_structure(self):
        from app.tools.github_analyzer import MockGitHubAnalyzer

        tool = MockGitHubAnalyzer()
        result = await tool.call({"repo_url": "https://github.com/org/repo"})
        assert "README" in str(result) or "readme" in str(result).lower()

    def test_is_read_only(self):
        from app.tools.github_analyzer import MockGitHubAnalyzer

        assert MockGitHubAnalyzer().is_read_only() is True


class TestRealGitHubAnalyzer:
    SKIP = os.getenv("RUN_REAL_TESTS", "0") != "1"

    @pytest.mark.asyncio
    async def test_fetches_real_repo_readme(self):
        if self.SKIP:
            pytest.skip("RUN_REAL_TESTS not set")
        from app.tools.github_analyzer import RealGitHubAnalyzer

        tool = RealGitHubAnalyzer()
        result = await tool.call({"repo_url": "https://github.com/huggingface/smolagents"})
        assert result.get("isError") is False
        assert "content" in result
        assert len(result["content"]) > 50

    @pytest.mark.asyncio
    async def test_invalid_url_returns_error(self):
        from app.tools.github_analyzer import RealGitHubAnalyzer

        tool = RealGitHubAnalyzer()
        result = await tool.call({"repo_url": "https://github.com/not-a-real-repo-xyz/does-not-exist-12345"})
        assert result.get("isError") is True

    @pytest.mark.asyncio
    async def test_missing_url_returns_error(self):
        from app.tools.github_analyzer import RealGitHubAnalyzer

        tool = RealGitHubAnalyzer()
        result = await tool.call({})
        assert result.get("isError") is True

    def test_real_is_read_only(self):
        from app.tools.github_analyzer import RealGitHubAnalyzer

        assert RealGitHubAnalyzer().is_read_only() is True
