import pytest

from app.core.workflow import LearnWorkflow
from app.llm.base import LLMRequest, LLMResponse
from app.memory.memory_store import MemoryStore
from app.memory.session_store import SessionStore
from app.tools.mock_learning_tools import MockSearchWebTool
from app.tools.registry import ToolRegistry


class RecordingLLMClient:
    def __init__(self):
        self.requests = []

    async def chat(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(content="LangGraph 是用于构建有状态 Agent 工作流的框架。")


@pytest.mark.asyncio
async def test_workflow_routes_runs_llm_and_persists_result(tmp_path):
    registry = ToolRegistry()
    registry.register(MockSearchWebTool())
    llm = RecordingLLMClient()
    workflow = LearnWorkflow(
        llm=llm,
        tools=registry,
        session_store=SessionStore(tmp_path / "sessions"),
        memory_store=MemoryStore(tmp_path / "memory"),
        session_id="session-1",
    )

    result = await workflow.run("我想学习 LangGraph")

    assert result.intent == "learn_concept"
    assert result.topic == "LangGraph"
    assert result.content == "LangGraph 是用于构建有状态 Agent 工作流的框架。"
    assert llm.requests[0].mode == "normal"
    assert llm.requests[0].tools == registry.to_api_schema()

    events = workflow.session_store.read_events("session-1")
    assert [event["type"] for event in events] == ["user_input", "route", "assistant_output"]
    assert workflow.memory_store.read("session-1_LangGraph").body == result.content
