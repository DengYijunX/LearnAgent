"""MCP 配置加载器 —— 读取 .mcp.json，连接服务器，注册工具。"""

import json
import os
import sys

from app.mcp.client import MCPClient
from app.mcp.adapter import MCPToolAdapter
from app.tools.registry import ToolRegistry


async def load_mcp_tools(registry: ToolRegistry, config_path: str | None = None) -> list[str]:
    """从配置文件加载 MCP 服务器，发现工具并注册到 ToolRegistry。返回服务器名列表。"""
    if config_path is None:
        # 从项目根目录找 .mcp.json
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(project_root, ".mcp.json")

    if not os.path.exists(config_path):
        return []

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

    servers = config.get("mcpServers", {})
    connected = []

    for server_name, server_config in servers.items():
        command = server_config.get("command", "")
        args = server_config.get("args", [])
        if not command:
            continue

        try:
            client = MCPClient(server_name, command, args)
            tools_defs = await client.connect()

            # 把每个 MCP 工具适配为 LearnAgent Tool
            for tool_def in tools_defs:
                adapter = MCPToolAdapter(
                    mcp_tool_def=tool_def,
                    call_fn=client.call_tool,
                    server_name=server_name,
                )
                registry.register(adapter)

            connected.append(server_name)
            print(f"  [MCP] {server_name}: {len(tools_defs)} 个工具已加载")
        except Exception as e:
            print(f"  [MCP] {server_name}: 连接失败 — {e}")

    return connected
