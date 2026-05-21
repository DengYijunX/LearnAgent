"""Tests for core/router.py."""


class TestInputRouter:
    def test_github_url_detected(self, router):
        result = router.route("https://github.com/huggingface/smolagents")
        assert result["intent"] == "analyze_repo"

    def test_http_url_detected(self, router):
        result = router.route("https://python.langchain.com/docs/")
        assert result["intent"] == "read_url"

    def test_learn_concept_detected(self, router):
        result = router.route("我想学习 LangGraph")
        assert result["intent"] == "learn_concept"

    def test_keyword_variations(self, router):
        keywords = ["学习", "了解", "学一下", "什么是", "讲讲"]
        for kw in keywords:
            result = router.route(f"{kw} Python 装饰器")
            assert result["intent"] == "learn_concept", f"failed for '{kw}'"

    def test_review_detected(self, router):
        result = router.route("复盘一下我最近学的")
        assert result["intent"] == "review"

    def test_unknown_falls_back_to_chat(self, router):
        result = router.route("今天天气不错")
        assert result["intent"] == "chat"

    def test_empty_input_returns_chat(self, router):
        result = router.route("")
        assert result["intent"] == "chat"

    def test_extracts_topic(self, router):
        result = router.route("我想学习 Rust 异步编程")
        assert result["topic"] is not None
        assert "rust" in result["topic"]  # normalized to lowercase

    def test_extracts_url_as_topic(self, router):
        result = router.route("https://github.com/org/repo")
        assert result["topic"] is not None


import pytest


@pytest.fixture
def router():
    from app.core.router import InputRouter

    return InputRouter()
