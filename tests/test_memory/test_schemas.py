from src.memory.schemas import (
    MemoryType, LearningEntry,
    MemoryIndex, UserProfileData, SessionEvent, ArtifactRecord,
)


def test_memory_type_enum():
    assert MemoryType.LEARNING_RECORD.value == "learning_record"
    assert MemoryType.USER_PROFILE.value == "user_profile"


def test_learning_entry_creation():
    entry = LearningEntry(
        id="learning-20260510-rag",
        topic="RAG",
        path="data/memory/learnings/2026-05-10-rag.md",
        tags=["rag", "retrieval"],
    )
    assert entry.topic == "RAG"
    assert len(entry.tags) == 2
    assert entry.type == MemoryType.LEARNING_RECORD


def test_memory_index_defaults():
    index = MemoryIndex()
    assert index.version == "1.1"
    assert index.learnings == []
    assert index.recent_topics == []


def test_memory_index_add_learning():
    index = MemoryIndex()
    entry = LearningEntry(
        id="learning-20260510-rag",
        topic="RAG",
        path="data/memory/learnings/2026-05-10-rag.md",
    )
    index.learnings.append(entry)
    index.recent_topics.append("RAG")
    assert len(index.learnings) == 1
    assert index.recent_topics == ["RAG"]


def test_user_profile_defaults():
    p = UserProfileData()
    assert p.version == "1.1"
    assert p.skills_known == []
    assert p.skills_learning == []
    assert p.preferred_difficulty == "beginner"
    assert p.preferred_language == "python"


def test_user_profile_serialization():
    p = UserProfileData(skills_known=["Python"], skills_learning=["RAG"])
    data = p.model_dump()
    assert data["skills_known"] == ["Python"]
    assert data["skills_learning"] == ["RAG"]
    assert "updated_at" in data


def test_session_event_creation():
    event = SessionEvent(type="user_input", query="什么是RAG")
    data = event.model_dump()
    assert data["type"] == "user_input"
    assert "time" in data


def test_artifact_record_creation():
    record = ArtifactRecord(
        artifact_id="artifact-20260510-rag",
        type="summary",
        topic="RAG",
        path="artifacts/summaries/2026-05-10-rag-summary.md",
    )
    assert record.artifact_id == "artifact-20260510-rag"
    assert record.type == "summary"
