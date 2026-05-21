"""SearchWeb 工具 —— 搜索技术资料。第一阶段返回 mock 结果。"""

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
