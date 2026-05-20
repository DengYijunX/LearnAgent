"""Environment-backed application settings."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


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


def load_settings(dotenv_path: Path | str = ".env") -> Settings:
    values = _load_dotenv(dotenv_path)
    return Settings(
        deepseek_api_key=_get_value("DEEPSEEK_API_KEY", "", values),
        deepseek_base_url=_get_value("DEEPSEEK_BASE_URL", "", values),
        deepseek_small_model=_get_value("DEEPSEEK_SMALL_MODEL", "", values),
        deepseek_large_model=_get_value("DEEPSEEK_LARGE_MODEL", "", values),
        model_mode=_get_value("LEARNAGENT_MODEL_MODE", "normal", values),
        llm_temperature=_get_float("LLM_TEMPERATURE", 0.2, values),
        llm_max_tokens=_get_int("LLM_MAX_TOKENS", 2048, values),
        run_real_tests=_get_bool("RUN_REAL_TESTS", False, values),
    )


def _load_dotenv(dotenv_path: Path | str) -> dict[str, str]:
    path = Path(dotenv_path)
    if not path.exists():
        return {}
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _get_value(name: str, default: str, dotenv_values: dict[str, str]) -> str:
    return os.getenv(name) or dotenv_values.get(name, default)


def _get_float(name: str, default: float, dotenv_values: dict[str, str]) -> float:
    value = _get_value(name, "", dotenv_values)
    if value is None or value == "":
        return default
    return float(value)


def _get_int(name: str, default: int, dotenv_values: dict[str, str]) -> int:
    value = _get_value(name, "", dotenv_values)
    if value is None or value == "":
        return default
    return int(value)


def _get_bool(name: str, default: bool, dotenv_values: dict[str, str]) -> bool:
    value = _get_value(name, "", dotenv_values)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
