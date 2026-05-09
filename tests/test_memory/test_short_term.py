import pytest
from unittest.mock import patch
from src.memory.short_term import ShortTermMemory


@pytest.fixture
async def memory(tmp_path):
    db_path = str(tmp_path / "test.db")
    chroma_path = str(tmp_path / "chroma")
    # 禁用 ChromaDB：onnxruntime 在部分 Windows 环境产生 C 级崩溃
    with patch("src.memory.short_term._chromadb_available", False):
        stm = ShortTermMemory(db_path, chroma_path)
        await stm.initialize()
        yield stm


@pytest.mark.asyncio
async def test_save_and_search(memory):
    await memory.save("RAG 是检索增强生成技术")
    await memory.save("LangGraph 是 agent 编排框架")
    # SQLite LIKE 搜索：用已保存内容中的关键词搜索
    results = await memory.search("RAG")
    assert len(results) > 0
    assert any("RAG" in r for r in results)


@pytest.mark.asyncio
async def test_list_recent(memory):
    await memory.save("条目 1")
    await memory.save("条目 2")
    recents = await memory.list_recent(limit=2)
    assert len(recents) == 2
