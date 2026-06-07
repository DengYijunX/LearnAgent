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

    @pytest.mark.asyncio
    async def test_adds_fallback_when_tools_fail_and_turns_exhausted(self):
        from app.llm.base import LLMClient
        from app.tools.base import Tool
        from app.tools.registry import ToolRegistry
        from app.core.agent_loop import agent_loop

        class ToolCallingLLM(LLMClient):
            async def chat(self, messages, system=None, tools=None, max_tokens=4096):
                return {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "read_url",
                            "arguments": '{"url":"https://example.com"}',
                        },
                    }],
                }

            async def stream_chat(self, messages, system=None, tools=None):
                yield {}

        class FailingReadUrl(Tool):
            name = "read_url"
            description = "fails"
            input_schema = {}

            async def call(self, tool_input, context=None):
                return {"isError": True, "error": "读取失败：timeout"}

        tools = ToolRegistry()
        tools.register(FailingReadUrl())
        messages = [{"role": "user", "content": "这里面最近的进展是什么"}]

        result = await agent_loop(messages=messages, llm=ToolCallingLLM(), tools=tools, max_turns=1)

        assert result["reason"] == "max_turns"
        final = result["messages"][-1]
        assert final["role"] == "assistant"
        assert "资料不足" in final["content"]
        assert "读取失败" in final["content"]


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


class TestToolResultSummary:
    def test_error_summary_preserves_path_tail(self):
        from app.core.agent_loop import _summarize_result

        summary, _extra = _summarize_result(
            "file_write",
            {
                "isError": True,
                "error": "写入失败：[Errno 13] Permission denied: 'E:\\code\\p\\pro\\LearnAgent\\storage\\workspace\\transformer\\self_attention_demo.py'",
            },
        )

        assert "Permission denied" in summary
        assert "self_attention_demo.py" in summary
