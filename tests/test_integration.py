import pytest
from src.main import app
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_learn_endpoint_simple_task():
    """模拟简单任务全链路"""
    with patch("src.router.router.ChatAnthropic") as RouterLLM:
        router_msg = AsyncMock()
        router_msg.content = '{"task_type": "simple", "reason": "查询概念"}'
        RouterLLM.return_value.ainvoke = AsyncMock(return_value=router_msg)

        with patch("src.agent.react_agent.ChatAnthropic") as ReactLLM:
            react_msg = AsyncMock()
            react_msg.content = '{"topic": "RAG", "core_concepts": ["检索", "增强"], "learning_points": ["第一步"], "related_techs": []}'
            ReactLLM.return_value.ainvoke = AsyncMock(return_value=react_msg)

            with patch("src.agent.react_agent.web_search") as mock_search:
                mock_search.return_value = [{"title": "t", "url": "http://x.com", "content": "c"}]
                with patch("src.agent.react_agent.fetch_content") as mock_fetch:
                    from src.tools.content_fetch import FetchedContent
                    mock_fetch.return_value = FetchedContent(url="http://x.com", content="content")
                    resp = client.post("/learn", json={"query": "什么是 RAG"})
                    assert resp.status_code == 200
                    data = resp.json()
                    assert data["task_type"] == "simple"
                    assert data["result"]["topic"] == "RAG"
