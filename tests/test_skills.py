"""Tests for skills/loader.py."""

import os
import tempfile


class TestSkillLoader:
    def test_load_valid_skill(self, skills_dir):
        from app.skills.loader import load_skill

        skill = load_skill(os.path.join(skills_dir, "learn-concept"))
        assert skill is not None
        assert skill["name"] == "learn-concept"
        assert "学习" in skill["description"]
        assert len(skill["body"]) > 0

    def test_load_nonexistent_returns_none(self, skills_dir):
        from app.skills.loader import load_skill

        assert load_skill(os.path.join(skills_dir, "no-such-skill")) is None

    def test_list_skills(self, skills_dir):
        from app.skills.loader import list_skills

        skills = list_skills(skills_dir)
        assert len(skills) >= 1
        names = {s["name"] for s in skills}
        assert "learn-concept" in names

    def test_empty_dir_returns_empty(self):
        from app.skills.loader import list_skills

        with tempfile.TemporaryDirectory() as d:
            assert list_skills(d) == []


import pytest


@pytest.fixture
def skills_dir():
    """返回项目 skills/ 目录路径。"""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "skills",
    )
