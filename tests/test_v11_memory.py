import json
import warnings

import pytest

from src.models.schemas import KnowledgeSummary


def test_safe_path_rejects_traversal(tmp_path):
    from src.utils.path_safety import safe_path

    with pytest.raises(ValueError):
        safe_path(tmp_path, "../escape.txt")


def test_learning_recorder_writes_index_and_metadata_only_search(tmp_path):
    from src.memory.learning_recorder import LearningRecorder

    recorder = LearningRecorder(tmp_path)
    summary = KnowledgeSummary(
        topic="RAG",
        core_concepts=["retrieval"],
        learning_points=["learn embeddings"],
        related_techs=["LangChain"],
    )

    entry = recorder.save_learning("RAG", summary, tags=["rag", "embedding"])
    results = recorder.search_memory("embedding")

    assert entry.path.startswith("data/memory/learnings/")
    assert (tmp_path / "memory" / "index.json").exists()
    assert (tmp_path / "memory" / "MEMORY.md").exists()
    assert results == [
        {
            "topic": "RAG",
            "path": entry.path,
            "type": "concept_summary",
            "tags": ["rag", "embedding"],
            "created_at": entry.created_at,
        }
    ]


def test_profile_update_does_not_promote_known_skill(tmp_path):
    from src.memory.user_profile import load_profile, mark_skill_known, update_profile

    path = tmp_path / "profile.json"
    profile = update_profile("RAG", path)

    assert "RAG" in profile.skills_learning
    assert "RAG" not in profile.skills_known

    promoted = mark_skill_known("RAG", path)
    assert "RAG" in promoted.skills_known
    assert "RAG" not in promoted.skills_learning
    assert load_profile(path).version == "1.1"


def test_session_logger_redacts_secrets_and_keeps_relative_paths(tmp_path):
    from src.memory.session_logger import SessionLogger

    logger = SessionLogger(tmp_path, mode="cli")
    logger.log(
        "plan_execute_complete",
        {
            "api_key": "sk-secret",
            "authorization": "Bearer secret-token",
            "note": "keyboard is normal text",
            "project_dir": str(tmp_path / "projects" / "demo"),
            "generated_files": [str(tmp_path / "projects" / "demo" / "main.py")],
        },
    )

    line = next((tmp_path / "sessions").glob("*-cli.jsonl")).read_text(encoding="utf-8")
    data = json.loads(line)

    assert data["data"]["api_key"] == "[REDACTED]"
    assert data["data"]["authorization"] == "[REDACTED]"
    assert data["data"]["note"] == "keyboard is normal text"
    assert data["data"]["project_dir"] == "projects/demo"
    assert data["data"]["generated_files"] == ["projects/demo/main.py"]


@pytest.mark.asyncio
async def test_short_term_memory_deprecated_without_external_storage(tmp_path):
    from src.memory.short_term import ShortTermMemory

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        memory = ShortTermMemory(str(tmp_path / "memory.db"), str(tmp_path / "chroma"))

    assert any(item.category is DeprecationWarning for item in caught)
    await memory.initialize()
    await memory.save("RAG 是检索增强生成技术")
    assert await memory.search("RAG") == ["RAG 是检索增强生成技术"]
