import json
from src.memory.user_profile import UserProfile, load_profile, save_profile


def test_load_profile_creates_default(tmp_path):
    path = str(tmp_path / "profile.json")
    profile = load_profile(path)
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
