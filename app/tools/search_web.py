"""SearchWeb 工具 —— 搜索技术资料。"""

from urllib.parse import urlparse
import os

from app.tools.base import Tool


UNSAFE_TITLE_KEYWORDS = (
    "暗网", "深网", "黑料", "吃瓜", "成人", "黄网站", "博彩", "赌场",
    "dvaj", "porn", "sex", "xxx", "casino", "bet365",
)
UNSAFE_DOMAINS = (
    "adult.example", "bad.example",
)


class MockSearchWeb(Tool):
    name = "search_web"
    description = "搜索技术名词、官方文档、教程、文章。输入 query 关键词。"
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词",
            }
        },
        "required": ["query"],
    }

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        query = tool_input.get("query", "")
        return {
            "content": f"[Mock 搜索结果] 关于「{query}」的资料：\n"
                       f"1. {query} 官方文档 - https://docs.example.com/{query}\n"
                       f"2. {query} 入门教程 - https://tutorial.example.com/{query}\n"
                       f"3. {query} 最佳实践 - https://best-practices.example.com/{query}",
            "isError": False,
        }


class RealSearchWeb(Tool):
    name = "search_web"
    description = "搜索互联网获取技术资料、官方文档、教程。输入 query 关键词和可选的 num 结果数量。"
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词",
            }
        },
        "required": ["query"],
    }

    def __init__(self, max_results: int = 5):
        self._max_results = max_results

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        query = (tool_input.get("query") or "").strip()
        if not query:
            return {"isError": True, "error": "请提供搜索关键词 query。"}

        try:
            from ddgs import DDGS

            proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("ALL_PROXY") or ""

            # 先尝试 auto（DuckDuckGo，质量最好），失败再降级到 mojeek,yandex
            backends = ["auto", "mojeek,yandex"]
            last_error = None

            for backend in backends:
                try:
                    results = []
                    filtered_count = 0
                    with DDGS(proxy=proxy or None, timeout=8) as ddgs:
                        for r in ddgs.text(query, max_results=self._max_results, backend=backend):
                            item = {
                                "title": r.get("title", ""),
                                "url": r.get("href", ""),
                                "snippet": r.get("body", ""),
                            }
                            if _is_unsafe_result(item):
                                filtered_count += 1
                                continue
                            results.append(item)
                    if results:
                        return {
                            "results": results,
                            "filtered_count": filtered_count,
                            "isError": False,
                        }
                except Exception as e:
                    last_error = str(e)
                    continue  # 当前后端失败，试下一个

            # 所有后端都失败
            return {"isError": True, "error": f"搜索失败：{last_error}"}
        except Exception as e:
            return {"isError": True, "error": f"搜索失败：{e}"}


def _is_unsafe_result(result: dict) -> bool:
    title = str(result.get("title") or "").lower()
    snippet = str(result.get("snippet") or "").lower()
    url = str(result.get("url") or "")
    host = urlparse(url).netloc.lower()

    haystack = f"{title} {snippet}"
    if any(keyword in haystack for keyword in UNSAFE_TITLE_KEYWORDS):
        return True
    return any(host == domain or host.endswith(f".{domain}") for domain in UNSAFE_DOMAINS)
