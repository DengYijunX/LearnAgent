import pytest
from unittest.mock import AsyncMock, patch
from src.agent.react_agent import run_react_agent


@pytest.mark.asyncio
async def test_react_agent_returns_knowledge_summary():
    """ReAct agent 应搜索 → 阅读 → 总结 并返回 KnowledgeSummary"""
    with patch("src.agent.react_agent.web_search") as mock_search:
        mock_search.return_value = [
            {"title": "RAG 介绍", "url": "https://example.com", "content": "RAG 是..."}
        ]
        with patch("src.agent.react_agent.fetch_content") as mock_fetch:
            from src.tools.content_fetch import FetchedContent
            mock_fetch.return_value = FetchedContent(url="https://example.com", content="RAG 即检索增强生成，结合了检索和 LLM 生成能力")
            with patch("src.agent.react_agent.ChatAnthropic") as MockLLM:
                mock_msg = AsyncMock()
                mock_msg.content = """{
                    "topic": "RAG",
                    "core_concepts": ["检索增强生成", "向量数据库", "Embedding"],
                    "learning_points": ["先理解 Embedding", "再学向量检索", "最后了解 RAG pipeline"],
                    "related_techs": ["LangChain", "LlamaIndex"]
                }"""
                MockLLM.return_value.ainvoke = AsyncMock(return_value=mock_msg)
                result = await run_react_agent("什么是 RAG")
                assert result.topic == "RAG"
                assert len(result.core_concepts) == 3
                assert mock_search.called


@pytest.mark.asyncio
async def test_react_agent_empty_search():
    """搜索结果为空时仍应返回 KnowledgeSummary"""
    with patch("src.agent.react_agent.web_search") as mock_search:
        mock_search.return_value = []
        with patch("src.agent.react_agent.ChatAnthropic") as MockLLM:
            mock_msg = AsyncMock()
            mock_msg.content = """{"topic": "", "core_concepts": [], "learning_points": [], "related_techs": []}"""
            MockLLM.return_value.ainvoke = AsyncMock(return_value=mock_msg)
            result = await run_react_agent("xxx罕见技术xxx")
            assert result.topic == ""
            assert result.core_concepts == []
