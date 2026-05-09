from src.config import Settings


def test_settings_defaults():
    # 跳过 .env 文件测试纯默认值
    s = Settings(_env_file=None)
    assert s.log_level == "DEBUG"
    assert s.llm_provider == "anthropic"
    assert s.deepseek_api_key == ""


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    s = Settings(_env_file=None)
    assert s.log_level == "INFO"
    assert s.llm_provider == "deepseek"
