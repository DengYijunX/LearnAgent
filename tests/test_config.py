from src.config import Settings


def test_settings_defaults():
    s = Settings()
    assert s.log_level == "DEBUG"
    assert s.anthropic_model_simple == "claude-sonnet-4-6"


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    s = Settings()
    assert s.log_level == "INFO"
