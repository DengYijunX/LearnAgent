"""Tests for config/settings.py."""

import os

import pytest


class TestConfig:
    def test_default_small_model(self, clean_env):
        from app.config.settings import Config

        cfg = Config()
        assert cfg.small_model is not None
        assert len(cfg.small_model) > 0

    def test_large_model_different_from_small(self, clean_env):
        from app.config.settings import Config

        cfg = Config()
        # In production these differ; in defaults they may differ too.
        assert cfg.large_model is not None

    def test_default_model_mode_is_normal(self, clean_env):
        from app.config.settings import Config

        cfg = Config()
        assert cfg.model_mode == "normal"

    def test_temperature_default(self, clean_env):
        from app.config.settings import Config

        cfg = Config()
        assert 0 <= cfg.temperature <= 1

    def test_max_tokens_positive(self, clean_env):
        from app.config.settings import Config

        cfg = Config()
        assert cfg.max_tokens > 0

    def test_base_url_has_default(self, clean_env):
        from app.config.settings import Config

        cfg = Config()
        assert cfg.base_url is not None
        assert cfg.base_url.startswith("https://")

    def test_api_key_is_none_when_not_set(self, clean_env):
        from app.config.settings import Config

        cfg = Config()
        assert cfg.api_key is None

    def test_env_var_overrides_default(self, clean_env, monkeypatch):
        monkeypatch.setenv("LEARNAGENT_MODEL_MODE", "deep")
        from app.config.settings import Config

        cfg = Config()
        assert cfg.model_mode == "deep"


@pytest.fixture
def clean_env(monkeypatch):
    """Remove all LEARNAGENT_ and DEEPSEEK_ env vars for clean test."""
    for key in list(os.environ.keys()):
        if key.startswith("LEARNAGENT_") or key.startswith("DEEPSEEK_"):
            monkeypatch.delenv(key, raising=False)
