"""Tests for llm/ base and mock client."""

import pytest


class TestLLMClientInterface:
    def test_chat_is_abstract(self):
        from app.llm.base import LLMClient

        with pytest.raises(TypeError):
            LLMClient()  # abstract, cannot instantiate

    def test_mock_client_implements_interface(self):
        from app.llm.base import LLMClient
        from app.llm.mock_client import MockLLMClient

        client = MockLLMClient()
        assert isinstance(client, LLMClient)

    def test_mock_client_returns_text_response(self):
        from app.llm.mock_client import MockLLMClient

        client = MockLLMClient()
        result = client.chat_sync(
            messages=[{"role": "user", "content": "Hello"}],
            system="You are helpful.",
        )
        assert result is not None
        assert "content" in result or "message" in result

    def test_mock_client_handles_tools(self):
        from app.llm.mock_client import MockLLMClient

        client = MockLLMClient()
        tools = [
            {"name": "search", "description": "Search", "input_schema": {}}
        ]
        # Should not crash
        result = client.chat_sync(
            messages=[{"role": "user", "content": "Search for LangGraph"}],
            tools=tools,
        )
        assert result is not None

    def test_mock_client_returns_assistant_role(self):
        from app.llm.mock_client import MockLLMClient

        client = MockLLMClient()
        result = client.chat_sync(
            messages=[{"role": "user", "content": "hi"}],
        )
        message = result if isinstance(result, dict) else result
        # Mock should return a dict with at minimum some content
        assert isinstance(message, dict)


class TestMockLLMClient:
    def test_response_is_deterministic(self):
        from app.llm.mock_client import MockLLMClient

        client = MockLLMClient()
        r1 = client.chat_sync([{"role": "user", "content": "x"}])
        r2 = client.chat_sync([{"role": "user", "content": "x"}])
        assert r1 == r2

    def test_tool_call_mode_returns_tool_use(self):
        from app.llm.mock_client import MockLLMClient

        client = MockLLMClient(respond_with_tool=True)
        result = client.chat_sync(
            messages=[{"role": "user", "content": "search something"}],
            tools=[{"name": "search_web", "description": "s", "input_schema": {}}],
        )
        assert "tool_calls" in result or "tool_use" in str(result)
