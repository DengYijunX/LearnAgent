"""MCP Client —— JSON-RPC 2.0 over stdio 协议客户端。

支持连接 MCP 服务器进程，发现工具并调用。
"""

import asyncio
import json
import os


class MCPClient:
    def __init__(self, name: str, command: str, args: list[str]):
        self.name = name
        self.command = command
        self.args = args
        self._proc = None
        self._id = 0
        self._pending = {}  # id -> Future

    @property
    def connected(self) -> bool:
        return self._proc is not None and self._proc.returncode is None

    async def connect(self) -> list[dict]:
        """启动 MCP 服务器进程，完成初始化握手，返回工具列表。"""
        self._proc = await asyncio.create_subprocess_exec(
            self.command, *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # 初始化
        init_result = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "LearnAgent", "version": "0.2.0"},
        })
        # 发送 initialized 通知
        self._send_notification("notifications/initialized", {})
        # 发现工具
        tools_result = await self._send_request("tools/list", {})
        return tools_result.get("tools", [])

    async def disconnect(self):
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._proc.kill()
        self._proc = None

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """调用 MCP 工具并返回结果。"""
        result = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        # MCP 返回 content 数组
        content = result.get("content", [])
        if content and isinstance(content, list):
            texts = []
            for item in content:
                if item.get("type") == "text":
                    texts.append(item.get("text", ""))
            return {"content": "\n".join(texts), "isError": result.get("isError", False)}
        return result

    async def _send_request(self, method: str, params: dict) -> dict:
        self._id += 1
        req = self._build_request(method, params, req_id=self._id)
        return await self._send_and_receive(req)

    def _send_notification(self, method: str, params: dict):
        msg = json.dumps({"jsonrpc": "2.0", "method": method, "params": params})
        if self._proc and self._proc.stdin:
            self._proc.stdin.write((msg + "\n").encode())
        # notification 不需要等待响应

    async def _send_and_receive(self, request: str) -> dict:
        if not self._proc or not self._proc.stdin or not self._proc.stdout:
            raise RuntimeError("MCP server not connected")
        # 发送
        self._proc.stdin.write((request + "\n").encode())
        await self._proc.stdin.drain()
        # 接收 —— 逐行读取直到拿到匹配的 JSON-RPC 响应
        while True:
            line = await asyncio.wait_for(self._proc.stdout.readline(), timeout=30)
            if not line:
                raise RuntimeError("MCP server closed connection")
            resp = self._parse_response(line.decode("utf-8"))
            if resp.get("id") == self._id:
                if "error" in resp:
                    raise RuntimeError(f"MCP error: {resp['error']}")
                return resp.get("result", {})

    def _build_request(self, method: str, params: dict, req_id: int | None = None) -> str:
        msg = {"jsonrpc": "2.0", "method": method, "params": params}
        if req_id is not None:
            msg["id"] = req_id
        return json.dumps(msg)

    def _parse_response(self, text: str) -> dict:
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {}
