"""Tools for long-term learning memory."""

from __future__ import annotations

from typing import Any

from app.memory.memory_store import MemoryEntry, MemoryStore
from app.tools.base import Tool, ToolResult


class SearchMemoryTool(Tool):
    name = "search_memory"
    description = "Search local long-term learning memory."
    input_schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }

    def __init__(self, store: MemoryStore):
        self._store = store

    async def call(self, tool_input: dict[str, Any], context: dict[str, Any]) -> ToolResult:
        query = tool_input.get("query", "")
        entries = self._store.search(query)
        content = "\n\n".join(_format_result(entry) for entry in entries)
        return ToolResult(
            content=content or "未找到相关长期记忆。",
            metadata={"query": query, "count": len(entries)},
        )


class SaveMemoryTool(Tool):
    name = "save_memory"
    description = "Save a long-term learning memory entry."
    input_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "type": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["name", "description", "type", "body"],
    }

    def __init__(self, store: MemoryStore):
        self._store = store

    def is_read_only(self) -> bool:
        return False

    async def call(self, tool_input: dict[str, Any], context: dict[str, Any]) -> ToolResult:
        entry = MemoryEntry(
            name=tool_input.get("name", ""),
            description=tool_input.get("description", ""),
            type=tool_input.get("type", "learning"),
            body=tool_input.get("body", ""),
        )
        path = self._store.save(entry)
        return ToolResult(
            content=f"已保存长期记忆：{entry.name}",
            metadata={"path": str(path), "name": entry.name},
        )


def _format_result(entry: MemoryEntry) -> str:
    return f"[{entry.type}] {entry.name}: {entry.description}\n{entry.body}"
