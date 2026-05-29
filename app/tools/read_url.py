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
                    "User-Agent": "Mozilla/5.0 (compatible; LearnAgent/0.2; +https://github.com/DengYijunX/LearnAgent)",
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
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            t = soup.title
            return t.get_text(strip=True)[:200] if t else ""
        except Exception:
            match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
            return match.group(1).strip()[:200] if match else ""

    @staticmethod
    def _extract_text(html: str) -> str:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # 移除不需要的标签
            for tag in soup(["script", "style", "noscript", "iframe", "nav", "footer", "header", "aside"]):
                tag.decompose()
            # 优先提取 <main> 或 <article> 内容
            main = soup.find("main") or soup.find("article") or soup.find("body")
            if main:
                text = main.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)
            # 清理空白行
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            return "\n".join(lines)
        except Exception:
            # regex fallback
            html = re.sub(r"<(script|style|noscript|iframe)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text)
            text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
            return text.strip()
