from src.memory.index_manager import IndexManager
from src.memory.learning_recorder import LearningRecorder
from src.models.schemas import KnowledgeSummary


def _make_summary(**kwargs) -> KnowledgeSummary:
    defaults = {
        "topic": "RAG",
        "core_concepts": ["检索增强生成", "向量数据库"],
        "learning_points": ["先理解Embedding", "再学检索"],
        "related_techs": ["LangChain", "ChromaDB"],
    }
    defaults.update(kwargs)
    return KnowledgeSummary(**defaults)


def test_save_learning_creates_file(tmp_path):
    base = str(tmp_path / "memory")
    im = IndexManager(base)
    recorder = LearningRecorder(im, learnings_dir=str(tmp_path / "memory/learnings"))
    summary = _make_summary()
    fm = recorder.save_learning("RAG", summary)
    assert fm.topic == "RAG"
    assert (recorder.learnings_dir).exists()


def test_save_learning_updates_index(tmp_path):
    base = str(tmp_path / "memory")
    im = IndexManager(base)
    recorder = LearningRecorder(im, learnings_dir=str(tmp_path / "memory/learnings"))
    summary = _make_summary()
    recorder.save_learning("RAG", summary)

    index = im.load()
    assert len(index.learnings) == 1
    assert index.learnings[0].topic == "RAG"


def test_save_learning_writes_frontmatter(tmp_path):
    base = str(tmp_path / "memory")
    im = IndexManager(base)
    recorder = LearningRecorder(im, learnings_dir=str(tmp_path / "memory/learnings"))
    summary = _make_summary()
    recorder.save_learning("RAG", summary)

    # 读取文件验证 YAML frontmatter
    files = list(recorder.learnings_dir.glob("*.md"))
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "id:" in content
    assert "topic: RAG" in content


def test_search_memory_finds_topic(tmp_path):
    base = str(tmp_path / "memory")
    im = IndexManager(base)
    recorder = LearningRecorder(im, learnings_dir=str(tmp_path / "memory/learnings"))
    recorder.save_learning("RAG", _make_summary())
    recorder.save_learning("FastAPI", _make_summary(topic="FastAPI"))

    results = recorder.search_memory("RAG", limit=5)
    assert len(results) == 1
    assert results[0]["topic"] == "RAG"
    # 只返回 metadata，不包含完整内容
    assert "content" not in results[0]


def test_search_memory_returns_empty_for_no_match(tmp_path):
    base = str(tmp_path / "memory")
    im = IndexManager(base)
    recorder = LearningRecorder(im, learnings_dir=str(tmp_path / "memory/learnings"))
    recorder.save_learning("RAG", _make_summary())

    results = recorder.search_memory("xyznotfound", limit=5)
    assert results == []


def test_get_recent_learnings(tmp_path):
    base = str(tmp_path / "memory")
    im = IndexManager(base)
    recorder = LearningRecorder(im, learnings_dir=str(tmp_path / "memory/learnings"))
    recorder.save_learning("RAG", _make_summary())
    recorder.save_learning("FastAPI", _make_summary(topic="FastAPI"))

    recent = recorder.get_recent_learnings(limit=2)
    assert len(recent) == 2
    topics = [r["topic"] for r in recent]
    assert "RAG" in topics
    assert "FastAPI" in topics
