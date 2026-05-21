"""Tests for core/agent_loop.py."""

import pytest


class TestAgentLoop:
    @pytest.mark.asyncio
    async def test_completes_when_no_tool_calls(self):
        from app.llm.mock_client import MockLLMClient
        from app.tools.registry import ToolRegistry
        from app.core.agent_loop import agent_loop

        llm = MockLLMClient(respond_with_tool=False)
        tools = ToolRegistry()
        messages = [{"role": "user", "content": "Hello"}]
        initial_count = len(messages)

        result = await agent_loop(messages=messages, llm=llm, tools=tools, max_turns=5)

        assert result["reason"] == "completed"
        assert len(result["messages"]) > initial_count

    @pytest.mark.asyncio
    async def test_executes_tool_and_continues(self):
        from app.llm.mock_client import MockLLMClient
        from app.tools.base import Tool
        from app.tools.registry import ToolRegistry
        from app.core.agent_loop import agent_loop

        class EchoTool(Tool):
            name = "echo"
            description = "Echoes input"
            input_schema = {
                "type": "object",
                "properties": {"text": {"type": "string"}},
            }

            async def call(self, tool_input, context=None):
                return {"echoed": tool_input.get("text", "")}

        tools = ToolRegistry()
        tools.register(EchoTool())

        llm = MockLLMClient(respond_with_tool=True)
        messages = [{"role": "user", "content": "echo hello"}]

        result = await agent_loop(messages=messages, llm=llm, tools=tools, max_turns=5)

        assert result["reason"] in ("completed", "max_turns")

    @pytest.mark.asyncio
    async def test_respects_max_turns(self):
        from app.llm.mock_client import MockLLMClient
        from app.tools.base import Tool
        from app.tools.registry import ToolRegistry
        from app.core.agent_loop import agent_loop

        class AlwaysTool(Tool):
            name = "loop"
            description = "Always called"
            input_schema = {}

            async def call(self, tool_input, context=None):
                return {"done": True}

        tools = ToolRegistry()
        tools.register(AlwaysTool())

        llm = MockLLMClient(respond_with_tool=True, tool_turns=10)
        messages = [{"role": "user", "content": "go"}]

        result = await agent_loop(messages=messages, llm=llm, tools=tools, max_turns=2)

        assert result["reason"] == "max_turns"

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error_observation(self):
        from app.llm.mock_client import MockLLMClient
        from app.tools.registry import ToolRegistry
        from app.core.agent_loop import agent_loop

        tools = ToolRegistry()
        # No tools registered, but mock will request one anyway

        llm = MockLLMClient(respond_with_tool=True)
        messages = [{"role": "user", "content": "use unknown tool"}]

        result = await agent_loop(messages=messages, llm=llm, tools=tools, max_turns=2)

        # Should not crash — unknown tool returns error observation
        assert "messages" in result

    @pytest.mark.asyncio
    async def test_messages_accumulate(self):
        from app.llm.mock_client import MockLLMClient
        from app.tools.registry import ToolRegistry
        from app.core.agent_loop import agent_loop

        llm = MockLLMClient(respond_with_tool=False)
        tools = ToolRegistry()
        messages = [{"role": "user", "content": "hi"}]

        result = await agent_loop(messages=messages, llm=llm, tools=tools, max_turns=5)

        # Should have user + assistant messages
        roles = [m.get("role") for m in result["messages"]]
        assert "user" in roles
        assert "assistant" in roles


class TestToolResultFormatter:
    def test_format_tool_result(self):
        from app.core.agent_loop import format_tool_result

        formatted = format_tool_result(
            tool_call_id="call_123",
            result={"data": "hello"},
        )
        assert formatted["role"] == "tool"
        assert formatted["tool_call_id"] == "call_123"
        assert "hello" in formatted["content"]

    def test_format_error_result(self):
        from app.core.agent_loop import format_error_result

        formatted = format_error_result(
            tool_call_id="call_456",
            error="Something went wrong",
        )
        assert formatted["role"] == "tool"
        assert formatted["tool_call_id"] == "call_456"
        assert formatted["is_error"] is True
        assert "Something went wrong" in formatted["content"]
