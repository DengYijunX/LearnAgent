from app.config.settings import Settings, load_settings


def test_load_settings_reads_deepseek_environment(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.example.test/v1")
    monkeypatch.setenv("DEEPSEEK_SMALL_MODEL", "deepseek-flash-id")
    monkeypatch.setenv("DEEPSEEK_LARGE_MODEL", "deepseek-pro-id")
    monkeypatch.setenv("LEARNAGENT_MODEL_MODE", "deep")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.3")
    monkeypatch.setenv("LLM_MAX_TOKENS", "4096")
    monkeypatch.setenv("RUN_REAL_TESTS", "1")

    settings = load_settings()

    assert settings.deepseek_api_key == "test-key"
    assert settings.deepseek_base_url == "https://api.example.test/v1"
    assert settings.deepseek_small_model == "deepseek-flash-id"
    assert settings.deepseek_large_model == "deepseek-pro-id"
    assert settings.model_mode == "deep"
    assert settings.llm_temperature == 0.3
    assert settings.llm_max_tokens == 4096
    assert settings.run_real_tests is True


def test_settings_defaults_do_not_guess_model_ids(monkeypatch):
    for name in (
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_BASE_URL",
        "DEEPSEEK_SMALL_MODEL",
        "DEEPSEEK_LARGE_MODEL",
        "LEARNAGENT_MODEL_MODE",
        "LLM_TEMPERATURE",
        "LLM_MAX_TOKENS",
        "RUN_REAL_TESTS",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = load_settings()

    assert settings == Settings()
    assert settings.deepseek_small_model == ""
    assert settings.deepseek_large_model == ""
    assert settings.model_mode == "normal"
    assert settings.llm_temperature == 0.2
    assert settings.llm_max_tokens == 2048
    assert settings.run_real_tests is False
