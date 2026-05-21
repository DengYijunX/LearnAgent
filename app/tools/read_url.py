"""ReadUrl 工具 —— 读取网页内容。"""

import re

from app.tools.base import Tool


class MockReadUrl(Tool):
    name = "read_url"
    description = "读取网页正文，提取主要内容。输入 url 地址。"
    input_schema = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "要读取的网页 URL",
            }
        },
        "required": ["url"],
    }

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        url = tool_input.get("url", "")
        return {
            "content": f"[Mock 网页内容] 来自 {url} 的正文摘要：\n"
                       f"这是关于该技术主题的核心介绍内容（mock）。\n"
                       f"主要包含概念解释、使用示例和注意事项。",
            "metadata": {
                "title": f"文档 - {url}",
                "source": url,
            },
        }


class RealReadUrl(Tool):
    name = "read_url"
    description = "读取指定 URL 的网页内容，提取正文文本。输入 url 地址。"
    input_schema = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "要读取的网页 URL",
            }
        },
        "required": ["url"],
    }

    def __init__(self, timeout: int = 15, max_content_length: int = 8000):
        self._timeout = timeout
        self._max_len = max_content_length

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        url = (tool_input.get("url") or "").strip()
        if not url:
            return {"isError": True, "error": "请提供 url 参数。"}

        try:
            import httpx

            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "LearnAgent/0.1",
                    "Accept": "text/html,application/xhtml+xml",
                })
                response.raise_for_status()
                html = response.text

            text = self._extract_text(html)
            title = self._extract_title(html)

            if len(text) > self._max_len:
                text = text[:self._max_len] + f"\n...(截断，原文共 {len(text)} 字符)"

            return {
                "content": text,
                "metadata": {
                    "title": title,
                    "source": url,
                },
                "isError": False,
            }
        except Exception as e:
            return {"isError": True, "error": f"读取失败：{e}"}

    @staticmethod
    def _extract_title(html: str) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()[:200]
        return ""

    @staticmethod
    def _extract_text(html: str) -> str:
        # Remove scripts and styles
        html = re.sub(r"<(script|style|noscript|iframe)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        # Decode common entities
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
        return text.strip()
