"""Common LLM client data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


Message = dict[str, Any]
ToolSchema = dict[str, Any]


@dataclass(frozen=True)
class LLMRequest:
    messages: list[Message]
    system: str | None = None
    tools: list[ToolSchema] | None = None
    mode: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


@dataclass(frozen=True)
class LLMResponse:
    content: str
    raw: dict[str, Any] = field(default_factory=dict)
    raw_json: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)


class LLMClient(Protocol):
    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Return one chat-completion response for the given request."""
