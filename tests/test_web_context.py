"""Web 学习上下文接口与协议测试。"""

import asyncio

import pytest

from app.server.session_manager import SessionManager


@pytest.mark.asyncio
async def test_session_manager_replaces_todo_snapshot():
    manager = SessionManager()
    session = await manager.create_session(topic="FastAPI")
    todos = [
        {
            "content": "阅读路由",
            "active_form": "正在阅读路由",
            "status": "in_progress",
        }
    ]

    updated = await manager.update_todos(session.session_id, todos)

    assert updated is not None
    assert updated.todos == todos
    assert (await manager.get_session(session.session_id)).todos == todos


@pytest.mark.asyncio
async def test_session_manager_copies_todo_input():
    manager = SessionManager()
    session = await manager.create_session()
    todos = [{"content": "练习", "status": "pending"}]

    await manager.update_todos(session.session_id, todos)
    todos[0]["status"] = "completed"

    assert session.todos[0]["status"] == "pending"


def test_bounded_memory_does_not_expose_unbounded_body():
    from app.server.routes import _bounded_memory

    item = {
        "name": "topic_x",
        "description": "学习记录",
        "type": "learning",
        "body": "x" * 1000,
    }

    result = _bounded_memory(item, body_limit=120)

    assert result["body"] == "x" * 120
    assert set(result) == {"name", "description", "type", "body"}


def test_format_todo_normalizes_active_form():
    from app.server.routes import _format_todo

    result = _format_todo(
        {"content": "读文档", "activeForm": "正在读文档", "status": "pending"}
    )

    assert result == {
        "content": "读文档",
        "active_form": "正在读文档",
        "status": "pending",
    }


def test_normalise_todos_rejects_invalid_status():
    from app.server.app import _normalise_todos

    todos = _normalise_todos([{"content": "A", "status": "unknown"}])

    assert todos == [{"content": "A", "active_form": None, "status": "pending"}]


@pytest.mark.asyncio
async def test_cancel_task_waits_for_cancellation():
    from app.server.app import _cancel_task

    started = asyncio.Event()

    async def worker():
        started.set()
        await asyncio.sleep(30)

    task = asyncio.create_task(worker())
    await started.wait()

    assert await _cancel_task(task) is True
    assert task.cancelled()


@pytest.mark.asyncio
async def test_todo_tool_publishes_snapshot_through_context():
    from app.core.session_context import current_todo_callback
    from app.tools.todo_tools import LearningTodoWrite

    snapshots = []

    async def capture(todos):
        snapshots.append(todos)

    token = current_todo_callback.set(capture)
    try:
        result = await LearningTodoWrite().call(
            {
                "todos": [
                    {
                        "content": "读文档",
                        "activeForm": "正在读文档",
                        "status": "in_progress",
                    }
                ]
            }
        )
    finally:
        current_todo_callback.reset(token)

    assert result["saved"] is True
    assert snapshots == [result["todos"]]
