import pytest
from unittest.mock import AsyncMock, patch
from src.agent.plan_execute_agent import build_plan_execute_graph


def test_graph_builds_successfully():
    """LangGraph 图应成功编译"""
    graph = build_plan_execute_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_graph_plan_node():
    """plan 节点应生成教学计划"""
    with patch("src.agent.plan_execute_agent.get_llm") as mock_get_llm:
        mock_msg = AsyncMock()
        mock_msg.content = """{"steps": [
            {"title": "安装 Redis", "description": "使用 Docker 安装", "files": {"docker-compose.yml": "..."}},
            {"title": "基础读写", "description": "SET/GET 操作", "files": {"main.py": "import redis\\nr = redis.Redis()\\nr.set('k', 'v')"}},
            {"title": "发布订阅", "description": "Pub/Sub 模式", "files": {"publisher.py": "...", "subscriber.py": "..."}}
        ]}"""
        mock_get_llm.return_value.ainvoke = AsyncMock(return_value=mock_msg)
        from src.agent.plan_execute_agent import plan_node
        from src.memory.working import create_initial_state
        state = create_initial_state("我要学 Redis")
        result = await plan_node(state)
        assert "plan" in result
        assert len(result["plan"]["steps"]) == 3
