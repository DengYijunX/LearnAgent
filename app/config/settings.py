"""Environment-backed application settings."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str = ""
    deepseek_base_url: str = ""
    deepseek_small_model: str = ""
    deepseek_large_model: str = ""
    model_mode: str = "normal"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 2048
    run_real_tests: bool = False


def load_settings() -> Settings:
    return Settings(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", ""),
        deepseek_small_model=os.getenv("DEEPSEEK_SMALL_MODEL", ""),
        deepseek_large_model=os.getenv("DEEPSEEK_LARGE_MODEL", ""),
        model_mode=os.getenv("LEARNAGENT_MODEL_MODE", "normal"),
        llm_temperature=_get_float("LLM_TEMPERATURE", 0.2),
        llm_max_tokens=_get_int("LLM_MAX_TOKENS", 2048),
        run_real_tests=_get_bool("RUN_REAL_TESTS", False),
    )


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
