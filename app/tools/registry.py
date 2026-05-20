"""Tool registry for lookup and LLM-facing schema export."""

from __future__ import annotations

from app.tools.base import Tool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def find(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def to_api_schema(self) -> list[dict]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
            if tool.is_enabled()
        ]
