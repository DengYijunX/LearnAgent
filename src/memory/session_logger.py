import json
import re
from pathlib import Path
from datetime import datetime
from src.logging_config import setup_logging

logger = setup_logging()

_SENSITIVE_FIELDS = {
    "api_key", "apikey", "api_secret", "token", "secret",
    "authorization", "password", "credential", "access_key",
}

_SENSITIVE_VALUE_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]+"),
    re.compile(r"Bearer\s+[a-zA-Z0-9\-\_\.]+"),
    re.compile(r"ghp_[a-zA-Z0-9]+"),
    re.compile(r"tvly-[a-zA-Z0-9]+"),
    re.compile(r"jina_[a-zA-Z0-9]+"),
]


def _redact(data: dict) -> dict:
    """脱敏：字段名命中 → 替换值；值命中密钥模式 → 替换。不误删普通文本。"""
    result = {}
    for k, v in data.items():
        if isinstance(v, str):
            key_lower = k.lower()
            if any(f in key_lower for f in _SENSITIVE_FIELDS):
                result[k] = "[REDACTED]"
            else:
                val = v
                for pat in _SENSITIVE_VALUE_PATTERNS:
                    val = pat.sub("[REDACTED]", val)
                result[k] = val
        else:
            result[k] = v
    return result


class SessionLogger:
    """追加 sessions/<date>-<mode>.jsonl，含脱敏。"""
    def __init__(self, base_dir: str = "data/sessions", mode: str = "cli"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        self.log_path = self.base_dir / f"{date_str}-{mode}.jsonl"

    def log(self, event_type: str, data: dict | None = None):
        data = data or {}
        safe_data = _redact(data)
        event = {"time": datetime.utcnow().isoformat(), "type": event_type, **safe_data}
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def log_learning_complete(self, topic: str, source: str = "react_agent"):
        self.log("learning_complete", {"topic": topic, "source": source})

    def log_plan_execute_complete(self, project_dir: str, generated_files: list[str],
                                  step_count: int):
        self.log("plan_execute_complete", {
            "project_dir": project_dir,
            "generated_files": generated_files,
            "step_count": step_count,
        })
