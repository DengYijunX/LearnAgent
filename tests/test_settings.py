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


def test_load_settings_reads_dotenv_file_without_overriding_environment(monkeypatch, tmp_path):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "\n".join(
            [
                "DEEPSEEK_API_KEY=from-dotenv",
                "DEEPSEEK_BASE_URL=https://dotenv.example/v1",
                "DEEPSEEK_SMALL_MODEL=dotenv-small",
                "DEEPSEEK_LARGE_MODEL=dotenv-large",
                "LEARNAGENT_MODEL_MODE=planning",
                "LLM_TEMPERATURE=0.4",
                "LLM_MAX_TOKENS=1024",
                "RUN_REAL_TESTS=true",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("DEEPSEEK_SMALL_MODEL", "from-env")

    settings = load_settings(dotenv_path=dotenv_path)

    assert settings.deepseek_api_key == "from-dotenv"
    assert settings.deepseek_base_url == "https://dotenv.example/v1"
    assert settings.deepseek_small_model == "from-env"
    assert settings.deepseek_large_model == "dotenv-large"
    assert settings.model_mode == "planning"
    assert settings.llm_temperature == 0.4
    assert settings.llm_max_tokens == 1024
    assert settings.run_real_tests is True
