"""MCP Tool Adapter —— 将 MCP 工具适配为 LearnAgent Tool 接口。"""

from app.tools.base import Tool


class MCPToolAdapter(Tool):
    def __init__(self, mcp_tool_def: dict, call_fn, server_name: str = "unknown"):
        self._def = mcp_tool_def
        self._call_fn = call_fn  # async function
        self._server = server_name
        self.name = f"mcp__{server_name}__{mcp_tool_def['name']}"
        self.description = mcp_tool_def.get("description", "")
        self.input_schema = mcp_tool_def.get("inputSchema", {})

    def is_read_only(self) -> bool:
        annotations = self._def.get("annotations", {})
        return annotations.get("readOnlyHint", True)

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        if not self._call_fn:
            return {"isError": True, "error": "MCP tool not connected"}
        return await self._call_fn(self._def["name"], tool_input)
