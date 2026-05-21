"""Workspace 工具 —— 文件读写和代码执行（参考 Claude Code 设计）。

所有路径操作受限于 workspace_root，防止逃逸。
RunCode 有超时和输出截断保护。
"""

import asyncio
import os

from app.tools.base import Tool


def _safe_path(workspace_root: str, user_path: str) -> str | None:
    """将用户输入路径解析为 workspace 内的绝对路径。拒绝逃逸。"""
    # 拒绝绝对路径
    if os.path.isabs(user_path):
        return None
    # 解析真实路径
    resolved = os.path.realpath(os.path.join(workspace_root, user_path))
    workspace_real = os.path.realpath(workspace_root)
    # 必须在 workspace 内
    if not resolved.startswith(workspace_real + os.sep) and resolved != workspace_real:
        return None
    return resolved


class FileWrite(Tool):
    name = "file_write"
    description = "在项目工作区创建或覆写文件。输入 path（相对路径）和 content（文件内容）。"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件在 workspace 内的相对路径，如 src/main.py"},
            "content": {"type": "string", "description": "要写入的文件内容"},
        },
        "required": ["path", "content"],
    }

    def __init__(self, workspace_root: str):
        self._root = workspace_root

    def is_read_only(self) -> bool:
        return False

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        path = tool_input.get("path", "")
        content = tool_input.get("content", "")
        safe = _safe_path(self._root, path)
        if safe is None:
            return {"isError": True, "error": f"路径非法或试图逃逸 workspace：{path}"}
        try:
            os.makedirs(os.path.dirname(safe), exist_ok=True)
            with open(safe, "w", encoding="utf-8") as f:
                f.write(content)
            return {"isError": False, "path": path, "written": True}
        except Exception as e:
            return {"isError": True, "error": f"写入失败：{e}"}


class FileRead(Tool):
    name = "file_read"
    description = "读取 workspace 内的文件内容。输入 path（相对路径）。"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件在 workspace 内的相对路径"},
        },
        "required": ["path"],
    }

    def __init__(self, workspace_root: str, max_length: int = 5000):
        self._root = workspace_root
        self._max_len = max_length

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        path = tool_input.get("path", "")
        safe = _safe_path(self._root, path)
        if safe is None:
            return {"isError": True, "error": f"路径非法：{path}"}
        if not os.path.isfile(safe):
            return {"isError": True, "error": f"文件不存在：{path}"}
        try:
            with open(safe, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if len(content) > self._max_len:
                content = content[:self._max_len] + f"\n...(截断，原文 {len(content)} 字符)"
            return {"isError": False, "path": path, "content": content}
        except Exception as e:
            return {"isError": True, "error": f"读取失败：{e}"}


class RunCode(Tool):
    name = "run_code"
    description = "在 workspace 内执行命令（如 python、node）。输入 command。限制超时和输出长度。"
    input_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的 shell 命令，如 python main.py"},
        },
        "required": ["command"],
    }

    def __init__(self, workspace_root: str, timeout: int = 10, max_output: int = 5000):
        self._root = workspace_root
        self._timeout = timeout
        self._max_output = max_output

    def is_read_only(self) -> bool:
        return False

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        command = tool_input.get("command", "")
        if not command.strip():
            return {"isError": True, "error": "请提供要执行的命令。"}
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._root,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self._timeout
                )
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                try:
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(), timeout=5
                    )
                except asyncio.TimeoutError:
                    stdout, stderr = b"", "(进程未能终止)".encode()
                return {
                    "isError": True,
                    "error": f"命令超时（{self._timeout}s）：{command[:80]}",
                    "stdout": stdout.decode("utf-8", errors="replace")[:500],
                    "stderr": stderr.decode("utf-8", errors="replace")[:500],
                }
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")
            if len(stdout_str) > self._max_output:
                stdout_str = stdout_str[:self._max_output] + "\n...(输出截断)"
            if len(stderr_str) > self._max_output:
                stderr_str = stderr_str[:self._max_output] + "\n...(输出截断)"
            return {
                "isError": proc.returncode != 0,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "returncode": proc.returncode,
            }
        except Exception as e:
            return {"isError": True, "error": f"执行失败：{e}"}


class ListFiles(Tool):
    name = "list_files"
    description = "列出 workspace 内的文件和目录结构。输入可选的 subdir（子目录）。"
    input_schema = {
        "type": "object",
        "properties": {
            "subdir": {"type": "string", "description": "可选的子目录路径"},
        },
        "required": [],
    }

    def __init__(self, workspace_root: str):
        self._root = workspace_root

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        subdir = tool_input.get("subdir", "") or ""
        target = os.path.join(self._root, subdir) if subdir else self._root
        safe = _safe_path(self._root, subdir) if subdir else self._root
        if safe is None:
            return {"isError": True, "error": f"路径非法：{subdir}"}
        try:
            lines = []
            for root, dirs, files in os.walk(safe):
                rel = os.path.relpath(root, self._root)
                if rel == ".":
                    rel = ""
                for d in dirs:
                    lines.append(f"  {os.path.join(rel, d)}/")
                for f in sorted(files):
                    lines.append(f"  {os.path.join(rel, f)}")
                # 限制深度
                depth = rel.count(os.sep) if rel else 0
                if depth >= 3:
                    dirs[:] = []
            content = "\n".join(lines[:100])
            return {"isError": False, "files": content if content else "(空)"}
        except Exception as e:
            return {"isError": True, "error": f"列出文件失败：{e}"}
