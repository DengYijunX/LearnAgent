"""Tests for real (non-mock) tool implementations.

These tests require network access and are skipped by default.
Set RUN_REAL_TESTS=1 to enable.
"""

import os
import pytest


NEED_REAL = os.getenv("RUN_REAL_TESTS", "0") != "1"
skip_if_no_real = pytest.mark.skipif(NEED_REAL, reason="RUN_REAL_TESTS not set")


class TestRealSearchWeb:
    @skip_if_no_real
    @pytest.mark.asyncio
    async def test_returns_results_for_query(self):
        from app.tools.search_web import RealSearchWeb

        tool = RealSearchWeb(max_results=3)
        result = await tool.call({"query": "Python asyncio tutorial"})
        assert "results" in result
        assert len(result["results"]) >= 1
        assert result.get("isError") is False

    @skip_if_no_real
    @pytest.mark.asyncio
    async def test_results_have_title_and_url(self):
        from app.tools.search_web import RealSearchWeb

        tool = RealSearchWeb(max_results=2)
        result = await tool.call({"query": "LangGraph"})
        for r in result.get("results", []):
            assert "title" in r
            assert "url" in r

    @pytest.mark.asyncio
    async def test_empty_query_returns_error(self):
        from app.tools.search_web import RealSearchWeb

        tool = RealSearchWeb()
        result = await tool.call({"query": ""})
        assert result.get("isError") is True

    def test_is_read_only(self):
        from app.tools.search_web import RealSearchWeb

        assert RealSearchWeb().is_read_only() is True


class TestRealReadUrl:
    @skip_if_no_real
    @pytest.mark.asyncio
    async def test_fetches_real_url(self):
        from app.tools.read_url import RealReadUrl

        tool = RealReadUrl()
        result = await tool.call({"url": "https://httpbin.org/html"})
        assert result.get("isError") is False
        assert "content" in result
        assert len(result["content"]) > 0

    @skip_if_no_real
    @pytest.mark.asyncio
    async def test_invalid_url_returns_error(self):
        from app.tools.read_url import RealReadUrl

        tool = RealReadUrl(timeout=10)
        result = await tool.call({"url": "https://this-domain-does-not-exist-12345.com"})
        assert result.get("isError") is True

    @pytest.mark.asyncio
    async def test_missing_url_returns_error(self):
        from app.tools.read_url import RealReadUrl

        tool = RealReadUrl()
        result = await tool.call({})
        assert result.get("isError") is True

    def test_is_read_only(self):
        from app.tools.read_url import RealReadUrl

        assert RealReadUrl().is_read_only() is True
