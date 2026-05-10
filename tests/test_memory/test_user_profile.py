import json
from src.memory.user_profile import load_profile, save_profile, update_profile, mark_skill_known, profile_summary


def test_load_profile_creates_default(tmp_path):
    path = str(tmp_path / "profile.json")
    profile = load_profile(path)
    assert profile.version == "1.1"
    assert profile.skills_known == []
    assert profile.skills_learning == []


def test_save_and_load_profile(tmp_path):
    path = str(tmp_path / "profile.json")
    profile = load_profile(path)
    profile.skills_known.append("Python")
    profile.preferred_difficulty = "intermediate"
    save_profile(profile, path)
    with open(path) as f:
        data = json.load(f)
    assert "Python" in data["skills_known"]
    assert data["preferred_difficulty"] == "intermediate"


def test_update_profile_adds_to_skills_learning(tmp_path):
    path = str(tmp_path / "profile.json")
    profile = load_profile(path)
    update_profile(profile, "RAG")
    assert "RAG" in profile.skills_learning
    # skills_known 不应自动更新
    assert "RAG" not in profile.skills_known


def test_mark_skill_known_moves_topic(tmp_path):
    path = str(tmp_path / "profile.json")
    profile = load_profile(path)
    update_profile(profile, "RAG")
    mark_skill_known(profile, "RAG")
    assert "RAG" in profile.skills_known
    assert "RAG" not in profile.skills_learning


def test_update_profile_dedup(tmp_path):
    path = str(tmp_path / "profile.json")
    profile = load_profile(path)
    update_profile(profile, "RAG")
    update_profile(profile, "RAG")
    assert profile.skills_learning.count("RAG") == 1
    assert profile.recent_topics.count("RAG") == 1


def test_profile_summary_new_user(tmp_path):
    path = str(tmp_path / "profile.json")
    profile = load_profile(path)
    assert "新用户" in profile_summary(profile)


def test_profile_summary_with_skills(tmp_path):
    path = str(tmp_path / "profile.json")
    profile = load_profile(path)
    profile.skills_known = ["Python"]
    profile.skills_learning = ["RAG"]
    summary = profile_summary(profile)
    assert "Python" in summary
    assert "RAG" in summary
