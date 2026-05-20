"""Tools for learning todo state."""

from __future__ import annotations

from typing import Any

from app.tasks.todo_store import LearningTodo, TodoStore
from app.tools.base import Tool, ToolResult


class LearningTodoWriteTool(Tool):
    name = "learning_todo_write"
    description = "Persist the current learning todo list for a session."
    input_schema = {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "activeForm": {"type": "string"},
                        "status": {"type": "string"},
                    },
                    "required": ["content", "activeForm", "status"],
                },
            }
        },
        "required": ["todos"],
    }

    def __init__(self, store: TodoStore):
        self._store = store

    def is_read_only(self) -> bool:
        return False

    async def call(self, tool_input: dict[str, Any], context: dict[str, Any]) -> ToolResult:
        session_id = context.get("session_id")
        if not session_id:
            return ToolResult(content="Missing session_id for learning todo write.", is_error=True)

        todos = [
            LearningTodo(
                content=item.get("content", ""),
                active_form=item.get("activeForm", ""),
                status=item.get("status", "pending"),
            )
            for item in tool_input.get("todos", [])
        ]
        self._store.save(session_id, todos)
        return ToolResult(
            content=f"已保存 {len(todos)} 个学习任务。",
            metadata={"session_id": session_id, "count": len(todos)},
        )
