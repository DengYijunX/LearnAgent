"""Tests for real (non-mock) tool implementations.

These tests require network access and are skipped by default.
Set RUN_REAL_TESTS=1 to enable.
"""

import os
import sys
import types

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

    @pytest.mark.asyncio
    async def test_retries_with_browser_headers_after_forbidden(self, monkeypatch):
        from app.tools.read_url import RealReadUrl

        requests = []

        class FakeResponse:
            def __init__(self, status_code, text):
                self.status_code = status_code
                self.text = text
                self.headers = {}

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise RuntimeError(f"HTTP {self.status_code}")

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def get(self, url, headers):
                requests.append(headers)
                if len(requests) == 1:
                    return FakeResponse(403, "")
                return FakeResponse(200, "<html><title>OK</title><main>正文</main></html>")

        fake_httpx = types.SimpleNamespace(AsyncClient=FakeAsyncClient)
        monkeypatch.setitem(sys.modules, "httpx", fake_httpx)

        result = await RealReadUrl().call({"url": "https://example.com/protected"})

        assert result.get("isError") is False
        assert result["content"] == "正文"
        assert len(requests) == 2
        assert "Chrome/" in requests[1]["User-Agent"]

    def test_is_read_only(self):
        from app.tools.read_url import RealReadUrl

        assert RealReadUrl().is_read_only() is True
