"""Tests for tools/base.py."""

import pytest


class TestToolInterface:
    def test_tool_has_name(self):
        from app.tools.base import Tool

        class MyTool(Tool):
            name = "my_tool"
            description = "A test tool"
            input_schema = {"type": "object", "properties": {}}

            async def call(self, tool_input, context=None):
                return {"result": "ok"}

        tool = MyTool()
        assert tool.name == "my_tool"

    def test_tool_has_description(self):
        from app.tools.base import Tool

        class MyTool(Tool):
            name = "my_tool"
            description = "A test tool"
            input_schema = {"type": "object", "properties": {}}

            async def call(self, tool_input, context=None):
                return {"result": "ok"}

        tool = MyTool()
        assert tool.description == "A test tool"

    def test_tool_has_input_schema(self):
        from app.tools.base import Tool

        schema = {"type": "object", "properties": {"q": {"type": "string"}}}

        class MyTool(Tool):
            name = "my_tool"
            description = "desc"
            input_schema = schema

            async def call(self, tool_input, context=None):
                return {"result": "ok"}

        tool = MyTool()
        assert tool.input_schema == schema

    def test_tool_is_read_only_defaults_true(self):
        from app.tools.base import Tool

        class MyTool(Tool):
            name = "t"
            description = "d"
            input_schema = {}

            async def call(self, tool_input, context=None):
                return {}

        tool = MyTool()
        assert tool.is_read_only() is True

    def test_tool_is_enabled_defaults_true(self):
        from app.tools.base import Tool

        class MyTool(Tool):
            name = "t"
            description = "d"
            input_schema = {}

            async def call(self, tool_input, context=None):
                return {}

        tool = MyTool()
        assert tool.is_enabled() is True

    def test_tool_call_must_be_implemented(self):
        from app.tools.base import Tool

        class IncompleteTool(Tool):
            name = "t"
            description = "d"
            input_schema = {}

        with pytest.raises(TypeError):
            IncompleteTool()  # missing abstract call()

    def test_tool_can_override_read_only(self):
        from app.tools.base import Tool

        class WriteTool(Tool):
            name = "write"
            description = "Writes files"
            input_schema = {}

            def is_read_only(self):
                return False

            async def call(self, tool_input, context=None):
                return {"written": True}

        tool = WriteTool()
        assert tool.is_read_only() is False
