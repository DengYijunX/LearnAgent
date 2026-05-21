"""Structured learning output schema."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any


@dataclass(frozen=True)
class LearningOutput:
    summary: str
    concepts: list[str] = field(default_factory=list)
    learning_path: list[str] = field(default_factory=list)
    practice_tasks: list[str] = field(default_factory=list)
    related_topics: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

    @classmethod
    def from_text(cls, text: str) -> "LearningOutput":
        stripped = text.strip()
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return cls(summary=stripped)
        if not isinstance(payload, dict):
            return cls(summary=stripped)
        return cls(
            summary=str(payload.get("summary") or stripped),
            concepts=_string_list(payload.get("concepts")),
            learning_path=_string_list(payload.get("learning_path")),
            practice_tasks=_string_list(payload.get("practice_tasks")),
            related_topics=_string_list(payload.get("related_topics")),
            sources=_string_list(payload.get("sources")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "concepts": self.concepts,
            "learning_path": self.learning_path,
            "practice_tasks": self.practice_tasks,
            "related_topics": self.related_topics,
            "sources": self.sources,
        }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
