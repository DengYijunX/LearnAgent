"""SearchWeb 工具 —— 搜索技术资料。"""

from app.tools.base import Tool


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

            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=self._max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    })
            return {
                "results": results,
                "isError": False,
            }
        except Exception as e:
            return {"isError": True, "error": f"搜索失败：{e}"}
