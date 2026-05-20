"""Base tool contracts for LearnAgent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolResult:
    content: str
    is_error: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "is_error": self.is_error,
            "metadata": self.metadata,
        }


class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]

    def is_read_only(self) -> bool:
        return True

    def is_enabled(self) -> bool:
        return True

    async def call(self, tool_input: dict[str, Any], context: dict[str, Any]) -> ToolResult:
        raise NotImplementedError
