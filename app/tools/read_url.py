"""Real URL reader tool using the Python standard library."""

from __future__ import annotations

import asyncio
from html.parser import HTMLParser
import re
from typing import Any, Awaitable, Callable
from urllib import request as urllib_request
from urllib.parse import urlparse

from app.tools.base import Tool, ToolResult


FetchResult = tuple[bytes, str]
Fetcher = Callable[[str, int], Awaitable[FetchResult]]


class ReadUrlTool(Tool):
    name = "read_url"
    description = "Read a public HTTP(S) page and extract visible text."
    input_schema = {
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    }

    def __init__(
        self,
        fetcher: Fetcher | None = None,
        timeout: int = 10,
        max_chars: int = 6000,
    ):
        self._fetcher = fetcher or _default_fetch
        self._timeout = timeout
        self._max_chars = max_chars

    async def call(self, tool_input: dict[str, Any], context: dict[str, Any]) -> ToolResult:
        url = tool_input.get("url", "")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return ToolResult(
                content="Only http and https URLs are supported.",
                is_error=True,
                metadata={"url": url},
            )

        try:
            body, content_type = await self._fetcher(url, self._timeout)
        except Exception as exc:
            return ToolResult(
                content=f"Failed to read URL: {exc}",
                is_error=True,
                metadata={"url": url},
            )

        encoding = _encoding_from_content_type(content_type) or "utf-8"
        html = body.decode(encoding, errors="replace")
        extracted = _extract_html_text(html)
        content = extracted.text[: self._max_chars]
        return ToolResult(
            content=content,
            metadata={
                "source": "real",
                "url": url,
                "title": extracted.title,
                "content_type": content_type,
                "truncated": len(extracted.text) > self._max_chars,
            },
        )


class _ExtractedHtml:
    def __init__(self, title: str, text: str):
        self.title = title
        self.text = text


class _VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._ignored_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs):
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str):
        if tag in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str):
        if self._ignored_depth:
            return
        stripped = data.strip()
        if not stripped:
            return
        if self._in_title:
            self.title_parts.append(stripped)
        else:
            self.text_parts.append(stripped)


def _extract_html_text(html: str) -> _ExtractedHtml:
    parser = _VisibleTextParser()
    parser.feed(html)
    title = _normalize_whitespace(" ".join(parser.title_parts))
    text = _normalize_whitespace("\n".join(parser.text_parts))
    return _ExtractedHtml(title=title, text=text)


def _normalize_whitespace(value: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def _encoding_from_content_type(content_type: str) -> str | None:
    match = re.search(r"charset=([^;]+)", content_type, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


async def _default_fetch(url: str, timeout: int) -> FetchResult:
    return await asyncio.to_thread(_fetch_blocking, url, timeout)


def _fetch_blocking(url: str, timeout: int) -> FetchResult:
    req = urllib_request.Request(
        url=url,
        headers={"User-Agent": "LearnAgent/0.1"},
        method="GET",
    )
    with urllib_request.urlopen(req, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        return response.read(), content_type
