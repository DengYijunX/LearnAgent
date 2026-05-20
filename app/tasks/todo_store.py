"""Local learning todo storage."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class LearningTodo:
    content: str
    active_form: str
    status: str


class TodoStore:
    def __init__(self, root: Path | str):
        self._root = Path(root)

    def save(self, session_id: str, todos: list[LearningTodo]) -> Path:
        self._root.mkdir(parents=True, exist_ok=True)
        path = self._path_for(session_id)
        path.write_text(
            json.dumps([asdict(todo) for todo in todos], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def load(self, session_id: str) -> list[LearningTodo]:
        path = self._path_for(session_id)
        if not path.exists():
            return []
        raw_items = json.loads(path.read_text(encoding="utf-8"))
        return [
            LearningTodo(
                content=item["content"],
                active_form=item["active_form"],
                status=item["status"],
            )
            for item in raw_items
        ]

    def _path_for(self, session_id: str) -> Path:
        return self._root / f"{session_id}_todos.json"
