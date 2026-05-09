import pytest
from unittest.mock import AsyncMock, patch
from src.router.router import route_task
from src.models.schemas import UserInput, TaskType


@pytest.mark.asyncio
async def test_route_keyword_to_simple():
    """技术名词查询应路由到简单任务"""
    with patch("src.router.router.get_llm") as mock_get_llm:
        mock_llm = mock_get_llm.return_value
        mock_msg = AsyncMock()
        mock_msg.content = '{"task_type": "simple", "reason": "这是一个概念问题"}'
        mock_llm.ainvoke = AsyncMock(return_value=mock_msg)
        decision = await route_task(UserInput(query="什么是 RAG"))
        assert decision.task_type == TaskType.SIMPLE


@pytest.mark.asyncio
async def test_route_learn_to_complex():
    """'我要学 X' 应路由到复杂任务"""
    with patch("src.router.router.get_llm") as mock_get_llm:
        mock_llm = mock_get_llm.return_value
        mock_msg = AsyncMock()
        mock_msg.content = '{"task_type": "complex", "reason": "用户要学新技术，需要生成教学项目"}'
        mock_llm.ainvoke = AsyncMock(return_value=mock_msg)
        decision = await route_task(UserInput(query="我要学 Redis"))
        assert decision.task_type == TaskType.COMPLEX


@pytest.mark.asyncio
async def test_route_llm_error_fallback_to_simple():
    """LLM 调用失败时降级为简单任务"""
    with patch("src.router.router.get_llm") as mock_get_llm:
        mock_llm = mock_get_llm.return_value
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("API 错误"))
        decision = await route_task(UserInput(query="测试"))
        assert decision.task_type == TaskType.SIMPLE
        assert "fallback" in decision.reason.lower()
