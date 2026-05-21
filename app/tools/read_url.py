"""ReadUrl 工具 —— 读取网页内容。第一阶段返回 mock 结果。"""

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
