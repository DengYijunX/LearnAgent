import os
from dataclasses import dataclass, field

# Lazy load .env only when this module is imported.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class Config:
    small_model: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_SMALL_MODEL", "deepseek-chat")
    )
    large_model: str = field(
        default_factory=lambda: os.getenv("DEEPSEEK_LARGE_MODEL", "deepseek-reasoner")
    )
    model_mode: str = field(
        default_factory=lambda: os.getenv("LEARNAGENT_MODEL_MODE", "normal")
    )
    temperature: float = field(
        default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.2"))
    )
    max_tokens: int = field(
        default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "2048"))
    )
    base_url: str = field(
        default_factory=lambda: os.getenv(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"
        )
    )
    api_key: str | None = field(
        default_factory=lambda: os.getenv("DEEPSEEK_API_KEY")
    )
    storage_base_dir: str = field(
        default_factory=lambda: os.getenv("LEARNAGENT_STORAGE_DIR", "storage")
    )
    run_real_tests: bool = field(
        default_factory=lambda: os.getenv("RUN_REAL_TESTS", "0") == "1"
    )


_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config
