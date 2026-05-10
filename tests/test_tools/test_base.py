import pytest
from src.tools.base import ToolSpec, ToolResult, BaseTool


class DummyTool(BaseTool):
    spec = ToolSpec(name="dummy", description="test", risk_level="low")

    async def run(self, **kwargs) -> ToolResult:
        return ToolResult.success("dummy", data=kwargs)


@pytest.mark.asyncio
async def test_tool_result_success():
    r = ToolResult.success("test", data={"x": 1})
    assert r.ok is True
    assert r.tool_name == "test"
    assert r.data == {"x": 1}


def test_tool_result_failure():
    r = ToolResult.failure("test", "something broke")
    assert r.ok is False
    assert r.error == "something broke"


def test_tool_result_serialization():
    r = ToolResult.success("test", data={"key": "value"}, metadata={"time_ms": 100})
    d = r.model_dump()
    assert d["ok"] is True
    assert d["metadata"]["time_ms"] == 100


def test_tool_spec_defaults():
    spec = ToolSpec(name="web_search")
    assert spec.name == "web_search"
    assert spec.risk_level == "low"
    assert spec.required_config == []


@pytest.mark.asyncio
async def test_base_tool_run():
    tool = DummyTool()
    r = await tool.run(query="hello")
    assert r.ok is True
    assert r.data == {"query": "hello"}


def test_tool_manager_register():
    from src.tools.manager import ToolManager
    mgr = ToolManager()
    mgr.register(DummyTool())
    tools = mgr.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "dummy"


@pytest.mark.asyncio
async def test_tool_manager_call():
    from src.tools.manager import ToolManager
    mgr = ToolManager()
    mgr.register(DummyTool())
    r = await mgr.call("dummy", query="test")
    assert r.ok is True


@pytest.mark.asyncio
async def test_tool_manager_unregistered():
    from src.tools.manager import ToolManager
    mgr = ToolManager()
    r = await mgr.call("nonexistent")
    assert r.ok is False
    assert "未注册" in r.error
