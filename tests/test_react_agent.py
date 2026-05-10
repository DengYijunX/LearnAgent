import pytest
from unittest.mock import AsyncMock, patch
from src.agent.react_agent import run_react_agent


def _decide_msg(action: str = "search") -> AsyncMock:
    m = AsyncMock()
    m.content = f'{{"action": "{action}", "reason": "test"}}'
    return m


def _summary_msg(**overrides) -> AsyncMock:
    defaults = {
        "topic": "RAG",
        "core_concepts": ["检索增强生成", "向量数据库", "Embedding"],
        "learning_points": ["先理解 Embedding", "再学向量检索", "最后了解 RAG pipeline"],
        "related_techs": ["LangChain", "LlamaIndex"],
    }
    defaults.update(overrides)
    import json
    m = AsyncMock()
    m.content = json.dumps(defaults)
    return m


@pytest.mark.asyncio
async def test_react_agent_with_search():
    """LLM 决定搜索 → 搜索 → 抓取 → 总结"""
    with patch("src.agent.react_agent.web_search") as mock_search:
        mock_search.return_value = [
            {"title": "RAG 介绍", "url": "https://example.com", "content": "RAG 是..."}
        ]
        with patch("src.agent.react_agent.fetch_content") as mock_fetch:
            from src.tools.content_fetch import FetchedContent
            mock_fetch.return_value = FetchedContent(url="https://example.com", content="RAG content")
            with patch("src.agent.react_agent.get_llm") as mock_get_llm:
                mock_get_llm.return_value.ainvoke = AsyncMock(side_effect=[
                    _decide_msg("search"),
                    _summary_msg(),
                ])
                result = await run_react_agent("什么是 RAG")
                assert result.topic == "RAG"
                assert len(result.core_concepts) == 3
                assert mock_search.called


@pytest.mark.asyncio
async def test_react_agent_answer_directly():
    """LLM 决定直接回答 → 不搜索，直接用知识回答"""
    with patch("src.agent.react_agent.web_search") as mock_search:
        with patch("src.agent.react_agent.get_llm") as mock_get_llm:
            mock_get_llm.return_value.ainvoke = AsyncMock(side_effect=[
                _decide_msg("answer"),
                _summary_msg(topic="高考时间", core_concepts=[], learning_points=["每年6月7-8日"], related_techs=[]),
            ])
            result = await run_react_agent("高考是什么时候")
            assert result.topic == "高考时间"
            assert not mock_search.called  # 不应该搜索


@pytest.mark.asyncio
async def test_react_agent_search_falls_back_to_knowledge():
    """搜索无结果 → 降级为知识回答"""
    with patch("src.agent.react_agent.web_search") as mock_search:
        mock_search.return_value = []
        with patch("src.agent.react_agent.get_llm") as mock_get_llm:
            mock_get_llm.return_value.ainvoke = AsyncMock(side_effect=[
                _decide_msg("search"),
                _summary_msg(),
            ])
            result = await run_react_agent("xxx罕见技术xxx")
            assert result.topic == "RAG"
            assert mock_search.called
