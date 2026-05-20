from app.tasks.todo_store import LearningTodo, TodoStore


def test_todo_store_saves_and_loads_todos(tmp_path):
    store = TodoStore(tmp_path / "tasks")
    todos = [
        LearningTodo(
            content="理解 LangGraph StateGraph",
            active_form="正在理解 LangGraph StateGraph",
            status="in_progress",
        ),
        LearningTodo(
            content="完成一个最小示例",
            active_form="正在完成一个最小示例",
            status="pending",
        ),
    ]

    path = store.save("session-1", todos)

    assert path.name == "session-1_todos.json"
    assert store.load("session-1") == todos


def test_todo_store_returns_empty_list_for_missing_session(tmp_path):
    store = TodoStore(tmp_path / "tasks")

    assert store.load("missing") == []
