import pytest

from app.tasks.todo_store import TodoStore
from app.tools.todo_tools import LearningTodoWriteTool


@pytest.mark.asyncio
async def test_learning_todo_write_tool_persists_todos(tmp_path):
    store = TodoStore(tmp_path / "tasks")
    tool = LearningTodoWriteTool(store)

    result = await tool.call(
        {
            "todos": [
                {
                    "content": "理解核心概念",
                    "activeForm": "正在理解核心概念",
                    "status": "in_progress",
                }
            ]
        },
        context={"session_id": "session-1"},
    )

    assert result.is_error is False
    assert "1 个学习任务" in result.content
    assert store.load("session-1")[0].content == "理解核心概念"


@pytest.mark.asyncio
async def test_learning_todo_write_tool_rejects_missing_session_id(tmp_path):
    tool = LearningTodoWriteTool(TodoStore(tmp_path / "tasks"))

    result = await tool.call({"todos": []}, context={})

    assert result.is_error is True
    assert "session_id" in result.content
