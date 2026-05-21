import pytest

from app.memory.memory_store import MemoryEntry, MemoryStore
from app.tools.memory_tools import SaveMemoryTool, SearchMemoryTool


@pytest.mark.asyncio
async def test_save_memory_tool_persists_memory_entry(tmp_path):
    store = MemoryStore(tmp_path / "memory")
    tool = SaveMemoryTool(store)

    result = await tool.call(
        {
            "name": "langgraph_intro",
            "description": "LangGraph 学习主题",
            "type": "learning",
            "body": "StateGraph 是核心概念。",
        },
        context={},
    )

    assert result.is_error is False
    assert "langgraph_intro" in result.content
    assert store.read("langgraph_intro").body == "StateGraph 是核心概念。"


@pytest.mark.asyncio
async def test_search_memory_tool_returns_matching_entries(tmp_path):
    store = MemoryStore(tmp_path / "memory")
    store.save(
        MemoryEntry(
            name="langgraph_intro",
            description="LangGraph 学习主题",
            type="learning",
            body="StateGraph 和条件边",
        )
    )
    tool = SearchMemoryTool(store)

    result = await tool.call({"query": "条件边"}, context={})

    assert result.is_error is False
    assert "langgraph_intro" in result.content
    assert result.metadata["count"] == 1
