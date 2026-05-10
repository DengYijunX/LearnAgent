import json
from pathlib import Path
from src.tools.artifact_writer import write_summary, write_project_doc
from src.models.schemas import KnowledgeSummary


def _make_summary(**kwargs) -> KnowledgeSummary:
    defaults = {
        "topic": "RAG",
        "core_concepts": ["检索增强生成"],
        "learning_points": ["理解Embedding"],
        "related_techs": ["LangChain"],
    }
    defaults.update(kwargs)
    return KnowledgeSummary(**defaults)


def test_write_summary_creates_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    summary = _make_summary()
    result_path = write_summary("RAG", summary)
    assert Path(result_path).exists()
    content = Path(result_path).read_text(encoding="utf-8")
    assert "RAG" in content
    assert "检索增强生成" in content


def test_write_summary_appends_index(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    summary = _make_summary()
    write_summary("RAG", summary)

    index_path = Path("data/artifacts_index.jsonl")
    assert index_path.exists()
    lines = index_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["type"] == "summary"
    assert record["topic"] == "RAG"


def test_write_project_doc(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result_path = write_project_doc("FastAPI", "## 项目简介\nFastAPI 入门")
    assert Path(result_path).exists()
    content = Path(result_path).read_text(encoding="utf-8")
    assert "FastAPI" in content
    assert "项目简介" in content


def test_write_summary_filename_has_date(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    summary = _make_summary()
    result_path = write_summary("RAG", summary)
    filename = Path(result_path).name
    # 文件名应包含日期和 summary
    assert "summary.md" in filename
    assert any(c.isdigit() for c in filename[:10])
