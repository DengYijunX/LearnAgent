import pytest

from app.tools.read_url import ReadUrlTool


@pytest.mark.asyncio
async def test_read_url_tool_extracts_title_and_visible_text():
    async def fake_fetch(url, timeout):
        assert url == "https://example.com/docs"
        assert timeout == 10
        return (
            b"""
            <html>
              <head>
                <title>Example Docs</title>
                <style>.hidden { display: none; }</style>
                <script>alert("x")</script>
              </head>
              <body>
                <h1>LangGraph Guide</h1>
                <p>StateGraph and conditional edges.</p>
              </body>
            </html>
            """,
            "text/html; charset=utf-8",
        )

    result = await ReadUrlTool(fetcher=fake_fetch).call(
        {"url": "https://example.com/docs"},
        context={},
    )

    assert result.is_error is False
    assert result.metadata["title"] == "Example Docs"
    assert result.metadata["url"] == "https://example.com/docs"
    assert "LangGraph Guide" in result.content
    assert "StateGraph and conditional edges." in result.content
    assert "alert" not in result.content
    assert ".hidden" not in result.content


@pytest.mark.asyncio
async def test_read_url_tool_rejects_non_http_url():
    result = await ReadUrlTool().call({"url": "file:///C:/secret.txt"}, context={})

    assert result.is_error is True
    assert "Only http and https URLs are supported" in result.content


@pytest.mark.asyncio
async def test_read_url_tool_returns_structured_fetch_error():
    async def fake_fetch(url, timeout):
        raise TimeoutError("timed out")

    result = await ReadUrlTool(fetcher=fake_fetch).call(
        {"url": "https://example.com/slow"},
        context={},
    )

    assert result.is_error is True
    assert "timed out" in result.content
    assert result.metadata["url"] == "https://example.com/slow"


@pytest.mark.asyncio
async def test_read_url_tool_truncates_long_text():
    async def fake_fetch(url, timeout):
        return (f"<html><body>{'x' * 50}</body></html>".encode("utf-8"), "text/html")

    result = await ReadUrlTool(fetcher=fake_fetch, max_chars=12).call(
        {"url": "https://example.com/long"},
        context={},
    )

    assert result.content == "x" * 12
    assert result.metadata["truncated"] is True
