from app.memory.memory_store import MemoryEntry, MemoryStore
from app.memory.session_store import SessionStore


def test_session_store_appends_and_reads_jsonl_events(tmp_path):
    store = SessionStore(tmp_path / "sessions")

    store.append_event("session-1", {"type": "message", "role": "user", "content": "hello"})
    store.append_event("session-1", {"type": "usage", "total_tokens": 3})

    assert store.read_events("session-1") == [
        {"type": "message", "role": "user", "content": "hello"},
        {"type": "usage", "total_tokens": 3},
    ]


def test_memory_store_writes_markdown_with_frontmatter(tmp_path):
    store = MemoryStore(tmp_path / "memory")
    entry = MemoryEntry(
        name="langgraph_intro",
        description="LangGraph 学习主题",
        type="learning",
        body="- 已开始学习 LangGraph\n- 下一步理解 StateGraph",
    )

    path = store.save(entry)

    assert path.name == "langgraph_intro.md"
    assert path.read_text(encoding="utf-8") == (
        "---\n"
        "name: langgraph_intro\n"
        "description: LangGraph 学习主题\n"
        "type: learning\n"
        "---\n\n"
        "- 已开始学习 LangGraph\n"
        "- 下一步理解 StateGraph\n"
    )


def test_memory_store_reads_saved_entry(tmp_path):
    store = MemoryStore(tmp_path / "memory")
    store.save(
        MemoryEntry(
            name="user_profile",
            description="用户学习偏好",
            type="user",
            body="用户偏好先讲原理，再给示例。",
        )
    )

    entry = store.read("user_profile")

    assert entry == MemoryEntry(
        name="user_profile",
        description="用户学习偏好",
        type="user",
        body="用户偏好先讲原理，再给示例。",
    )
