import pytest

from app.tools.base import Tool, ToolResult
from app.tools.registry import ToolRegistry


class EchoTool(Tool):
    name = "echo"
    description = "Echo the input text."
    input_schema = {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    }

    async def call(self, tool_input, context):
        return ToolResult(content=tool_input["text"])


class DisabledTool(Tool):
    name = "disabled"
    description = "Disabled test tool."
    input_schema = {"type": "object", "properties": {}}

    def is_enabled(self):
        return False

    async def call(self, tool_input, context):
        return ToolResult(content="disabled")


def test_registry_registers_and_finds_tool():
    registry = ToolRegistry()
    tool = EchoTool()

    registry.register(tool)

    assert registry.find("echo") is tool
    assert registry.find("missing") is None


def test_registry_rejects_duplicate_tool_names():
    registry = ToolRegistry()
    registry.register(EchoTool())

    with pytest.raises(ValueError, match="already registered"):
        registry.register(EchoTool())


def test_registry_exports_enabled_tools_as_api_schema():
    registry = ToolRegistry()
    registry.register(EchoTool())
    registry.register(DisabledTool())

    assert registry.to_api_schema() == [
        {
            "name": "echo",
            "description": "Echo the input text.",
            "input_schema": EchoTool.input_schema,
        }
    ]


def test_tool_result_can_represent_structured_errors():
    result = ToolResult(content="failed", is_error=True, metadata={"code": "bad_input"})

    assert result.to_dict() == {
        "content": "failed",
        "is_error": True,
        "metadata": {"code": "bad_input"},
    }
