"""Markdown + frontmatter long-term memory storage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


SAFE_NAME_PATTERN = re.compile(r"[^a-zA-Z0-9_.-]+")


@dataclass(frozen=True)
class MemoryEntry:
    name: str
    description: str
    type: str
    body: str


class MemoryStore:
    def __init__(self, root: Path | str):
        self._root = Path(root)

    def save(self, entry: MemoryEntry) -> Path:
        self._root.mkdir(parents=True, exist_ok=True)
        path = self._path_for(entry.name)
        path.write_text(_format_entry(entry), encoding="utf-8")
        return path

    def read(self, name: str) -> MemoryEntry | None:
        path = self._path_for(name)
        if not path.exists():
            return None
        return _parse_entry(path.read_text(encoding="utf-8"))

    def list_entries(self) -> list[MemoryEntry]:
        if not self._root.exists():
            return []
        return [
            _parse_entry(path.read_text(encoding="utf-8"))
            for path in sorted(self._root.glob("*.md"))
        ]

    def search(self, query: str) -> list[MemoryEntry]:
        normalized_query = query.lower()
        return [
            entry
            for entry in self.list_entries()
            if normalized_query in _entry_search_text(entry).lower()
        ]

    def _path_for(self, name: str) -> Path:
        safe_name = SAFE_NAME_PATTERN.sub("_", name).strip("_")
        if not safe_name:
            raise ValueError("Memory entry name cannot be empty")
        return self._root / f"{safe_name}.md"


def _format_entry(entry: MemoryEntry) -> str:
    body = entry.body.rstrip()
    return (
        "---\n"
        f"name: {entry.name}\n"
        f"description: {entry.description}\n"
        f"type: {entry.type}\n"
        "---\n\n"
        f"{body}\n"
    )


def _parse_entry(content: str) -> MemoryEntry:
    if not content.startswith("---\n"):
        raise ValueError("Memory entry is missing frontmatter")
    _, frontmatter, body = content.split("---\n", 2)
    values = {}
    for line in frontmatter.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return MemoryEntry(
        name=values.get("name", ""),
        description=values.get("description", ""),
        type=values.get("type", ""),
        body=body.strip(),
    )


def _entry_search_text(entry: MemoryEntry) -> str:
    return "\n".join([entry.name, entry.description, entry.type, entry.body])
