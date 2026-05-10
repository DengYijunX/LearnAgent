import json
from pathlib import Path
from src.memory.session_logger import SessionLogger, _redact


def test_redact_field_name():
    result = _redact({"api_key": "sk-abc123", "query": "hello"})
    assert result["api_key"] == "[REDACTED]"
    assert result["query"] == "hello"


def test_redact_value_pattern():
    result = _redact({"authorization": "Bearer xyz-token-123"})
    assert result["authorization"] == "[REDACTED]"


def test_redact_sk_pattern_in_value():
    result = _redact({"content": "key=sk-12345"})
    assert "[REDACTED]" in result["content"]


def test_redact_does_not_touch_normal_text():
    result = _redact({"description": "this keyboard is nice"})
    assert "keyboard" in result["description"]


def test_session_logger_writes_jsonl(tmp_path):
    log_dir = str(tmp_path / "sessions")
    sl = SessionLogger(log_dir)
    sl.log("user_input", {"query": "什么是RAG"})
    sl.log("route", {"task_type": "simple"})

    files = list(Path(log_dir).glob("*.jsonl"))
    assert len(files) == 1
    lines = files[0].read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        data = json.loads(line)
        assert "time" in data
        assert "type" in data


def test_session_logger_redacts_api_key(tmp_path):
    log_dir = str(tmp_path / "sessions")
    sl = SessionLogger(log_dir)
    sl.log("tool_call", {"tool": "web_search", "api_key": "sk-secret"})

    files = list(Path(log_dir).glob("*.jsonl"))
    line = json.loads(files[0].read_text(encoding="utf-8").strip())
    assert line["api_key"] == "[REDACTED]"
