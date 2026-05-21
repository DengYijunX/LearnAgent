"""Tests for Skill injection into system prompt."""

import os

import pytest


class TestSkillInjection:
    def test_load_all_three_skills(self, skills_dir):
        from app.skills.loader import list_skills

        skills = list_skills(skills_dir)
        names = {s["name"] for s in skills}
        assert "learn-concept" in names
        assert "read-repo" in names
        assert "review-progress" in names

    def test_intent_to_skill_mapping(self, skill_map):
        assert skill_map.get("learn_concept") == "learn-concept"
        assert skill_map.get("analyze_repo") == "read-repo"
        assert skill_map.get("review") == "review-progress"
        assert skill_map.get("chat") is None

    def test_skill_body_injected_to_system_prompt(self, skill_map, skills_dir):
        from app.skills.loader import load_skill
        from app.context.context_builder import build_system_prompt

        skill = load_skill(os.path.join(skills_dir, "learn-concept"))
        body = skill["body"]
        prompt = build_system_prompt(
            current_topic="Rust",
            intent="learn_concept",
            skill_body=body,
        )
        assert "SKILL" in prompt or "流程" in prompt or "步骤" in prompt

    def test_no_skill_for_chat_intent(self, skill_map, skills_dir):
        from app.context.context_builder import build_system_prompt

        prompt = build_system_prompt(
            current_topic=None,
            intent="chat",
            skill_body=None,
        )
        # Should not contain skill instructions
        assert "SKILL" not in prompt


INTENT_TO_SKILL = {
    "learn_concept": "learn-concept",
    "analyze_repo": "read-repo",
    "review": "review-progress",
}


@pytest.fixture
def skill_map():
    return INTENT_TO_SKILL


@pytest.fixture
def skills_dir():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "skills",
    )
