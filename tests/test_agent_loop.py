import pytest

from app.core.agent_loop import run_agent_loop
from app.llm.base import LLMRequest, LLMResponse
from app.tools.base import Tool, ToolResult
from app.tools.registry import ToolRegistry


class SequencedLLMClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    async def chat(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return self._responses.pop(0)


class EchoTool(Tool):
    name = "echo"
    description = "Echo text."
    input_schema = {"type": "object", "properties": {"text": {"type": "string"}}}

    async def call(self, tool_input, context):
        return ToolResult(content=f"echo:{tool_input['text']}")


class ContextTool(Tool):
    name = "context"
    description = "Return context values."
    input_schema = {"type": "object", "properties": {}}

    async def call(self, tool_input, context):
        return ToolResult(
            content=f"{context['session_id']}|{context['current_topic']}"
        )


@pytest.mark.asyncio
async def test_agent_loop_executes_standard_tool_call_and_finishes():
    registry = ToolRegistry()
    registry.register(EchoTool())
    llm = SequencedLLMClient(
        [
            LLMResponse(
                content="",
                tool_calls=[
                    {
                        "id": "call_1",
                        "function": {
                            "name": "echo",
                            "arguments": '{"text": "hello"}',
                        },
                    }
                ],
            ),
            LLMResponse(content="完成：echo:hello"),
        ]
    )

    result = await run_agent_loop(
        llm=llm,
        tools=registry,
        messages=[{"role": "user", "content": "say hello"}],
        system_prompt="你是 LearnAgent",
    )

    assert result.reason == "completed"
    assert result.final_content == "完成：echo:hello"
    assert llm.requests[0].tools == registry.to_api_schema()
    assert llm.requests[1].tools == []
    assert llm.requests[1].messages[-2]["role"] == "assistant"
    assert llm.requests[1].messages[-2]["tool_calls"][0]["id"] == "call_1"
    assert llm.requests[1].messages[-1]["role"] == "tool"
    assert llm.requests[1].messages[-1]["tool_call_id"] == "call_1"
    assert llm.requests[1].messages[-1]["content"] == "echo:hello"


@pytest.mark.asyncio
async def test_agent_loop_supports_json_action_fallback():
    registry = ToolRegistry()
    registry.register(EchoTool())
    llm = SequencedLLMClient(
        [
            LLMResponse(content='{"action": "echo", "arguments": {"text": "hi"}}'),
            LLMResponse(content="完成：echo:hi"),
        ]
    )

    result = await run_agent_loop(
        llm=llm,
        tools=registry,
        messages=[{"role": "user", "content": "say hi"}],
    )

    assert result.final_content == "完成：echo:hi"
    assert llm.requests[1].tools == []
    assert llm.requests[1].messages[-1]["role"] == "user"
    assert llm.requests[1].messages[-1]["content"] == "echo:hi"


@pytest.mark.asyncio
async def test_agent_loop_returns_tool_error_for_unknown_tool():
    llm = SequencedLLMClient(
        [
            LLMResponse(content='{"action": "missing_tool", "arguments": {}}'),
            LLMResponse(content="工具不可用"),
        ]
    )

    result = await run_agent_loop(
        llm=llm,
        tools=ToolRegistry(),
        messages=[{"role": "user", "content": "try tool"}],
    )

    assert result.reason == "completed"
    assert "Unknown tool" in llm.requests[1].messages[-1]["content"]


@pytest.mark.asyncio
async def test_agent_loop_passes_context_to_tools():
    registry = ToolRegistry()
    registry.register(ContextTool())
    llm = SequencedLLMClient(
        [
            LLMResponse(content='{"action": "context", "arguments": {}}'),
            LLMResponse(content="完成"),
        ]
    )

    await run_agent_loop(
        llm=llm,
        tools=registry,
        messages=[{"role": "user", "content": "use context"}],
        tool_context={"session_id": "session-1", "current_topic": "LangGraph"},
    )

    assert llm.requests[1].messages[-1]["content"] == "session-1|LangGraph"
