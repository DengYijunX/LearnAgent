"""Tests for MCP client and tool adapter."""

import json
import pytest


class TestMCPClient:
    def test_client_has_connect_and_disconnect(self):
        from app.mcp.client import MCPClient

        client = MCPClient("test", "echo", [])
        assert client.name == "test"
        assert not client.connected

    def test_client_format_initialize(self):
        from app.mcp.client import MCPClient

        client = MCPClient("test", "echo", [])
        msg = client._build_request("tools/list", {}, req_id=1)
        parsed = json.loads(msg)
        assert parsed["jsonrpc"] == "2.0"
        assert parsed["method"] == "tools/list"
        assert parsed["id"] == 1

    def test_client_parse_response(self):
        from app.mcp.client import MCPClient

        client = MCPClient("test", "echo", [])
        resp = '{"jsonrpc":"2.0","id":1,"result":{"tools":[]}}'
        result = client._parse_response(resp)
        assert result["result"]["tools"] == []

    def test_client_parse_error(self):
        from app.mcp.client import MCPClient

        client = MCPClient("test", "echo", [])
        resp = '{"jsonrpc":"2.0","id":1,"error":{"code":-32601,"message":"Method not found"}}'
        result = client._parse_response(resp)
        assert "error" in result


class TestMCPToolAdapter:
    def test_adapter_creates_learnagent_tool(self):
        from app.mcp.adapter import MCPToolAdapter

        mcp_tool_def = {
            "name": "read_file",
            "description": "Read a file from the filesystem",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"],
            },
        }
        adapter = MCPToolAdapter(mcp_tool_def, call_fn=None, server_name="test")
        assert adapter.name == "mcp__test__read_file"
        assert "Read a file" in adapter.description
        assert adapter.is_read_only() is True  # default

    def test_adapter_respects_read_only_hint(self):
        from app.mcp.adapter import MCPToolAdapter

        mcp_tool_def = {
            "name": "write_file",
            "description": "Write a file",
            "inputSchema": {},
            "annotations": {"readOnlyHint": False},
        }
        adapter = MCPToolAdapter(mcp_tool_def, call_fn=None, server_name="filesystem")
        assert adapter.is_read_only() is False

    def test_adapter_namespace(self):
        from app.mcp.adapter import MCPToolAdapter

        mcp_tool_def = {"name": "search", "description": "s", "inputSchema": {}}
        adapter = MCPToolAdapter(mcp_tool_def, call_fn=None, server_name="brave-search")
        assert adapter.name == "mcp__brave-search__search"
