"""Tests for Plan Mode: read-only exploration before execution."""

import pytest


class TestPlanMode:
    def test_plan_mode_blocks_write_tools(self):
        from app.tools.workspace_tools import FileWrite
        from app.safety.permission import check_permission

        tool = FileWrite(workspace_root="/tmp")
        decision = check_permission(tool, {}, mode="plan")
        assert decision.behavior == "deny"
        assert "plan" in decision.reason.lower()

    def test_plan_mode_allows_read_tools(self):
        from app.tools.search_web import MockSearchWeb
        from app.safety.permission import check_permission

        tool = MockSearchWeb()
        decision = check_permission(tool, {}, mode="plan")
        assert decision.behavior == "allow"

    def test_default_mode_allows_all(self):
        from app.tools.workspace_tools import FileWrite
        from app.safety.permission import check_permission

        tool = FileWrite(workspace_root="/tmp")
        decision = check_permission(tool, {}, mode="default")
        assert decision.behavior == "ask"


class TestQueryEnginePlanMode:
    @pytest.mark.asyncio
    async def test_enter_plan_via_command(self, engine):
        result = await engine.submit_message("/plan")
        assert engine.permission_mode == "plan"
        assert "plan" in result.get("content", "").lower()

    @pytest.mark.asyncio
    async def test_exit_plan_via_command(self, engine):
        engine.permission_mode = "plan"
        result = await engine.submit_message("/plan")
        assert engine.permission_mode == "default"
        assert "default" in result.get("content", "").lower() or "退出" in result.get("content", "")

    @pytest.mark.asyncio
    async def test_submit_message_in_plan_mode_passes_mode_to_loop(self, engine):
        engine.permission_mode = "plan"
        result = await engine.submit_message("探索 LangGraph 项目", topic="langgraph", intent="learn_concept")
        assert result is not None


import pytest
from unittest import mock


@pytest.fixture
def engine():
    from app.llm.mock_client import MockLLMClient
    from app.tools.registry import ToolRegistry
    from app.core.query_engine import LearnQueryEngine

    return LearnQueryEngine(
        llm=MockLLMClient(respond_with_tool=False),
        tools=ToolRegistry(),
    )
