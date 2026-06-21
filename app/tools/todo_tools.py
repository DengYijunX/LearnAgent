"""LearningTodoWrite 工具 —— 维护当前学习任务进度。"""

import inspect

from app.core.session_context import current_todo_callback
from app.tools.base import Tool


class LearningTodoWrite(Tool):
    name = "learning_todo_write"
    description = "维护当前学习任务进度。输入 todos 数组，每项含 content、status（pending/in_progress/completed）。"
    input_schema = {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "description": "学习任务列表",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "activeForm": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed"],
                        },
                    },
                },
            }
        },
        "required": ["todos"],
    }

    def is_read_only(self) -> bool:
        return False

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        todos = []
        for item in tool_input.get("todos", []):
            status = item.get("status", "pending")
            if status not in {"pending", "in_progress", "completed"}:
                status = "pending"
            todos.append({
                "content": str(item.get("content", "")).strip(),
                "active_form": item.get("active_form", item.get("activeForm")),
                "status": status,
            })

        result = {
            "saved": True,
            "count": len(todos),
            "todos": todos,
        }
        callback = current_todo_callback.get()
        if callback:
            pending = callback(todos)
            if inspect.isawaitable(pending):
                await pending
        return result
