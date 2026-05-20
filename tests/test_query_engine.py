"""Tests for core/query_engine.py."""

import pytest


class TestLearnQueryEngine:
    @pytest.mark.asyncio
    async def test_submit_message_returns_result(self, engine):
        result = await engine.submit_message("我想学习 Python")
        assert result is not None

    @pytest.mark.asyncio
    async def test_messages_accumulate_across_turns(self, engine):
        await engine.submit_message("第一个问题")
        count_after_first = len(engine.messages)

        await engine.submit_message("第二个问题")
        count_after_second = len(engine.messages)

        assert count_after_second > count_after_first

    @pytest.mark.asyncio
    async def test_handles_slash_help(self, engine):
        result = await engine.submit_message("/help")
        assert result is not None
        # Should not add /help to messages
        assert not any(
            m.get("content") == "/help" for m in engine.messages
            if m.get("role") == "user"
        )

    @pytest.mark.asyncio
    async def test_session_id_is_unique(self, engine):
        from app.core.query_engine import LearnQueryEngine
        from app.llm.mock_client import MockLLMClient
        from app.tools.registry import ToolRegistry

        e2 = LearnQueryEngine(
            llm=MockLLMClient(),
            tools=ToolRegistry(),
        )
        assert engine.session_id != e2.session_id

    @pytest.mark.asyncio
    async def test_message_has_user_role_after_submit(self, engine):
        await engine.submit_message("测试消息")
        user_msgs = [
            m for m in engine.messages if m.get("role") == "user"
        ]
        assert len(user_msgs) >= 1


@pytest.fixture
def engine():
    from app.llm.mock_client import MockLLMClient
    from app.tools.registry import ToolRegistry
    from app.core.query_engine import LearnQueryEngine

    return LearnQueryEngine(
        llm=MockLLMClient(respond_with_tool=False),
        tools=ToolRegistry(),
    )
