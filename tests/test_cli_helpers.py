"""Tests for CLI helper behavior in app/main.py."""

import os
import tempfile


def test_format_permission_value_preserves_full_command():
    from app.main import _format_permission_value

    command = "python self_attention_demo.py --explain --verbose"

    assert _format_permission_value("command", command) == command


def test_format_permission_value_summarizes_long_content():
    from app.main import _format_permission_value

    content = "a" * 300
    formatted = _format_permission_value("content", content)

    assert "300 字符" in formatted
    assert len(formatted) < 220


def test_sync_workspace_tools_for_route_registers_topic_workspace():
    from app.main import _sync_workspace_tools_for_route
    from app.tools.registry import ToolRegistry

    with tempfile.TemporaryDirectory() as storage:
        tools = ToolRegistry()

        workspace = _sync_workspace_tools_for_route(
            tools=tools,
            storage_base=storage,
            topic="Transformer",
            intent="learn_concept",
        )

        file_write = tools.find("file_write")
        assert file_write is not None
        assert file_write._root == os.path.join(storage, "workspace", "transformer")
        assert workspace == file_write._root


def test_sync_workspace_tools_for_route_ignores_chat_without_topic():
    from app.main import _sync_workspace_tools_for_route
    from app.tools.registry import ToolRegistry

    with tempfile.TemporaryDirectory() as storage:
        tools = ToolRegistry()

        workspace = _sync_workspace_tools_for_route(
            tools=tools,
            storage_base=storage,
            topic=None,
            intent="chat",
        )

        assert workspace is None
        assert tools.find("file_write") is None
