"""Session 存储 —— JSONL 格式，每行一条记录，便于追加和恢复。"""

import json
import os


class SessionStore:
    def __init__(self, base_dir: str):
        self._base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _path(self, session_id: str) -> str:
        return os.path.join(self._base_dir, f"{session_id}.jsonl")

    def append_message(self, session_id: str, message: dict) -> None:
        with open(self._path(session_id), "a", encoding="utf-8") as f:
            f.write(json.dumps(message, ensure_ascii=False) + "\n")

    def get_messages(self, session_id: str) -> list[dict]:
        path = self._path(session_id)
        if not os.path.exists(path):
            return []
        messages = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        messages.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return messages
