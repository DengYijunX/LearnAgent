"""LearningTodoWrite 工具 —— 维护当前学习任务进度。"""

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
        todos = tool_input.get("todos", [])
        return {
            "saved": True,
            "count": len(todos),
            "todos": todos,
        }
