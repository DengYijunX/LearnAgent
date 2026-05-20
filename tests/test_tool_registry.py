"""Tests for tools/registry.py."""

import pytest


class TestToolRegistry:
    def test_register_and_find(self):
        from app.tools.base import Tool
        from app.tools.registry import ToolRegistry

        class MyTool(Tool):
            name = "my_tool"
            description = "desc"
            input_schema = {}

            async def call(self, tool_input, context=None):
                return {}

        registry = ToolRegistry()
        registry.register(MyTool())
        found = registry.find("my_tool")
        assert found is not None
        assert found.name == "my_tool"

    def test_find_missing_returns_none(self):
        from app.tools.registry import ToolRegistry

        registry = ToolRegistry()
        assert registry.find("nonexistent") is None

    def test_to_api_schema(self):
        from app.tools.base import Tool
        from app.tools.registry import ToolRegistry

        class ReadTool(Tool):
            name = "read"
            description = "Reads a file"
            input_schema = {
                "type": "object",
                "properties": {"path": {"type": "string"}},
            }

            async def call(self, tool_input, context=None):
                return {}

        registry = ToolRegistry()
        registry.register(ReadTool())
        schemas = registry.to_api_schema()
        assert len(schemas) == 1
        assert schemas[0]["name"] == "read"
        assert schemas[0]["description"] == "Reads a file"
        assert "path" in schemas[0]["input_schema"]["properties"]

    def test_disabled_tool_not_in_schema(self):
        from app.tools.base import Tool
        from app.tools.registry import ToolRegistry

        class DisabledTool(Tool):
            name = "disabled"
            description = "x"
            input_schema = {}

            def is_enabled(self):
                return False

            async def call(self, tool_input, context=None):
                return {}

        registry = ToolRegistry()
        registry.register(DisabledTool())
        schemas = registry.to_api_schema()
        assert len(schemas) == 0

    def test_multiple_tools_in_schema(self):
        from app.tools.base import Tool
        from app.tools.registry import ToolRegistry

        class ToolA(Tool):
            name = "a"; description = "A"; input_schema = {}
            async def call(self, tool_input, context=None): return {}

        class ToolB(Tool):
            name = "b"; description = "B"; input_schema = {}
            async def call(self, tool_input, context=None): return {}

        registry = ToolRegistry()
        registry.register(ToolA())
        registry.register(ToolB())
        schemas = registry.to_api_schema()
        assert len(schemas) == 2
        names = {s["name"] for s in schemas}
        assert names == {"a", "b"}

    def test_duplicate_name_overwrites(self):
        from app.tools.base import Tool
        from app.tools.registry import ToolRegistry

        class V1(Tool):
            name = "t"; description = "v1"; input_schema = {}
            async def call(self, tool_input, context=None): return {}

        class V2(Tool):
            name = "t"; description = "v2"; input_schema = {}
            async def call(self, tool_input, context=None): return {}

        registry = ToolRegistry()
        registry.register(V1())
        registry.register(V2())
        assert registry.find("t").description == "v2"
