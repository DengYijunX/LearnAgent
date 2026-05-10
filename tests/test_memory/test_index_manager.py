import json
from src.memory.index_manager import IndexManager


def test_init_creates_index(tmp_path):
    base = str(tmp_path / "memory")
    mgr = IndexManager(base)
    index = mgr.load()
    assert index.version == "1.1"
    assert index.learnings == []


def test_save_and_reload(tmp_path):
    base = str(tmp_path / "memory")
    mgr = IndexManager(base)
    index = mgr.load()
    index.recent_topics.append("RAG")
    mgr.save(index)
    assert (mgr.index_path).exists()
    reloaded = json.loads(mgr.index_path.read_text())
    assert "RAG" in reloaded["recent_topics"]


def test_add_learning(tmp_path):
    base = str(tmp_path / "memory")
    mgr = IndexManager(base)
    mgr.add_learning("RAG", "data/memory/learnings/rag.md", tags=["rag", "retrieval"])
    index = mgr.load()
    assert len(index.learnings) == 1
    assert index.learnings[0].topic == "RAG"


def test_add_learning_dedup(tmp_path):
    base = str(tmp_path / "memory")
    mgr = IndexManager(base)
    mgr.add_learning("RAG", "data/memory/learnings/rag1.md")
    mgr.add_learning("RAG", "data/memory/learnings/rag2.md")
    index = mgr.load()
    assert len(index.learnings) == 1


def test_render_memory_md(tmp_path):
    base = str(tmp_path / "memory")
    mgr = IndexManager(base)
    mgr.add_learning("RAG", "data/memory/learnings/rag.md", tags=["rag"])
    md = mgr.memory_md_path.read_text(encoding="utf-8")
    assert "LearnAgent Memory Index" in md
    assert "RAG" in md


def test_memory_md_line_limit(tmp_path):
    base = str(tmp_path / "memory")
    mgr = IndexManager(base)
    # 添加 25 条学习记录，MEMORY.md 应只展示最近 20 条
    for i in range(25):
        mgr.add_learning(f"Topic{i}", f"data/memory/learnings/topic{i}.md")
    md = mgr.memory_md_path.read_text(encoding="utf-8")
    lines = md.split("\n")
    assert len(lines) <= 200


def test_get_recent_learnings(tmp_path):
    base = str(tmp_path / "memory")
    mgr = IndexManager(base)
    mgr.add_learning("RAG", "data/memory/learnings/rag.md")
    mgr.add_learning("FastAPI", "data/memory/learnings/fastapi.md")
    recent = mgr.get_recent_learnings(limit=2)
    assert len(recent) == 2
