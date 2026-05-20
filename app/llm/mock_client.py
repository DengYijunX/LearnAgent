"""Deterministic LLM client for tests and local architecture checks."""

from __future__ import annotations

from app.llm.base import LLMRequest, LLMResponse


class MockLLMClient:
    def __init__(self, response: LLMResponse | None = None):
        self._response = response
        self.requests: list[LLMRequest] = []

    async def chat(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        if self._response is not None:
            return self._response
        return LLMResponse(content="Mock response from LearnAgent LLM client.")
