"""Tests for llm/model_selector.py."""


class TestModelSelector:
    def test_normal_mode_returns_small_model(self, selector):
        model = selector.select("normal")
        assert model == selector.small_model

    def test_summary_mode_returns_small_model(self, selector):
        model = selector.select("summary")
        assert model == selector.small_model

    def test_lightweight_mode_returns_small_model(self, selector):
        model = selector.select("lightweight")
        assert model == selector.small_model

    def test_deep_mode_returns_large_model(self, selector):
        model = selector.select("deep")
        assert model == selector.large_model

    def test_planning_mode_returns_large_model(self, selector):
        model = selector.select("planning")
        assert model == selector.large_model

    def test_repo_analysis_mode_returns_large_model(self, selector):
        model = selector.select("repo_analysis")
        assert model == selector.large_model

    def test_unknown_mode_falls_back_to_small_model(self, selector):
        model = selector.select("nonexistent_mode")
        assert model == selector.small_model

    def test_select_for_intent_learn_concept(self, selector):
        model = selector.select_for_intent("learn_concept")
        assert model == selector.small_model

    def test_select_for_intent_analyze_repo(self, selector):
        model = selector.select_for_intent("analyze_repo")
        assert model == selector.large_model

    def test_unknown_intent_uses_default_mode(self, selector):
        model = selector.select_for_intent("unknown_intent")
        assert model == selector.small_model


import pytest


@pytest.fixture
def selector():
    from app.llm.model_selector import ModelSelector

    return ModelSelector(small_model="small-model", large_model="large-model")
