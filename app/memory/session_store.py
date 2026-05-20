"""JSONL session storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SessionStore:
    def __init__(self, root: Path | str):
        self._root = Path(root)

    def append_event(self, session_id: str, event: dict[str, Any]) -> Path:
        self._root.mkdir(parents=True, exist_ok=True)
        path = self._path_for(session_id)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False))
            handle.write("\n")
        return path

    def read_events(self, session_id: str) -> list[dict[str, Any]]:
        path = self._path_for(session_id)
        if not path.exists():
            return []
        events = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(json.loads(line))
        return events

    def _path_for(self, session_id: str) -> Path:
        return self._root / f"{session_id}.jsonl"
