"""Workspace 工具 —— 文件读写和代码执行（参考 Claude Code 设计）。

所有路径操作受限于 workspace_root，防止逃逸。
RunCode 有超时和输出截断保护。
"""

import asyncio
import logging
import os
import re

from app.tools.base import Tool

logger = logging.getLogger(__name__)


def _safe_path(workspace_root: str, user_path: str) -> str | None:
    """将用户输入路径解析为 workspace 内的绝对路径。拒绝逃逸。"""
    # 拒绝空路径
    if not user_path or not user_path.strip():
        return None
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
    description = "在项目工作区创建或覆写文件。输入 path（相对项目根目录的路径）和 content（文件内容）。路径示例：storage/workspace/hello.py、storage/workspace/utils/helper.py。"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件相对项目根目录的路径，如 storage/workspace/hello.py、storage/workspace/scripts/deploy.sh"},
            "content": {"type": "string", "description": "要写入的文件内容"},
        },
        "required": ["path", "content"],
    }

    def __init__(self, workspace_root: str):
        self._root = workspace_root

    def is_read_only(self) -> bool:
        return False

    RESERVED_NAMES = {"app.py", "main.py"}

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        path = (tool_input.get("path") or "").strip()
        content = tool_input.get("content")
        if not path:
            return {"isError": True, "error": "缺少 path 参数。请提供要写入文件的路径，如 hello.py"}
        if content is None:
            return {"isError": True, "error": "缺少 content 参数。请提供要写入的文件内容"}
        # 自动去除 storage/workspace/ 前缀（LLM 可能被描述误导）
        normalized_input = path.replace("\\", "/").lstrip("./")
        if normalized_input.startswith("storage/workspace/"):
            path = normalized_input[len("storage/workspace/"):]
        # 拒绝保留文件名
        basename = os.path.basename(path)
        if basename.lower() in self.RESERVED_NAMES:
            return {"isError": True, "error": f"禁止使用保留文件名 {basename}。请用描述性名称如 learn_flask.py"}
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
    description = "读取项目文件内容。输入 path（相对项目根目录的路径），如 storage/workspace/hello.py。"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件相对项目根目录的路径，如 storage/workspace/hello.py"},
        },
        "required": ["path"],
    }

    def __init__(self, workspace_root: str, max_length: int = 5000):
        self._root = workspace_root
        self._max_len = max_length

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        path = (tool_input.get("path") or "").strip()
        if not path:
            return {"isError": True, "error": "缺少 path 参数。请提供要读取文件的路径，如 hello.py"}
        # 自动去除 storage/workspace/ 前缀
        normalized_input = path.replace("\\", "/").lstrip("./")
        if normalized_input.startswith("storage/workspace/"):
            path = normalized_input[len("storage/workspace/"):]
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

    def __init__(self, workspace_root: str, timeout: int = 60, max_output: int = 5000, use_docker: bool = False):
        self._root = workspace_root
        self._timeout = timeout
        self._max_output = max_output
        self._use_docker = use_docker

    def is_read_only(self) -> bool:
        return False

    DANGEROUS = [
        "rm -rf", "rm -r", "sudo", "shutdown", "reboot", "format",
        "> /dev/sda", "mkfs", "dd if=", ":(){ :|:& };:",
        "python -m venv", "virtualenv", "pipenv", "poetry new",
        "git push", "git reset --hard", "git clean",
    ]

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        command = tool_input.get("command", "")
        if not command.strip():
            return {"isError": True, "error": "请提供要执行的命令。"}
        cmd_lower = command.lower()
        for d in self.DANGEROUS:
            if d in cmd_lower:
                return {"isError": True, "error": f"禁止执行危险或不需要的命令（含 '{d}'）。请用其他方式。"}

        if self._use_docker:
            return await self._docker_exec(command)
        return await self._subprocess_exec(command)

    async def _docker_exec(self, command: str) -> dict:
        """在 Docker 容器中执行命令（沙箱隔离）。"""
        abs_root = os.path.abspath(self._root)
        # Escape double quotes in command for bash -c
        escaped = command.replace('\\', '\\\\').replace('"', '\\"')
        docker_cmd = (
            f"docker run --rm "
            f"--memory=256m --cpus=1 "
            f"--network=none "
            f"-v \"{abs_root}:/workspace\" "
            f"-w /workspace "
            f"python:3.11-slim bash -c \"{escaped}\""
        )
        return await self._subprocess_exec(docker_cmd)

    _PORT_RE = re.compile(r"(?:port[= ]+|:)(\d{4,5})")

    async def _subprocess_exec(self, command: str) -> dict:
        # 检测是否为服务类命令 → 后台模式
        try:
            from app.process_manager import looks_like_server, get_process_manager
        except ImportError:
            looks_like_server = lambda c: False
            get_process_manager = lambda: None

        pm = get_process_manager()

        if looks_like_server(command) and pm is not None:
            # 后台模式：启动后立即返回，不等待
            port = None
            m = self._PORT_RE.search(command)
            if m:
                port = int(m.group(1))
            try:
                from app.core.session_context import current_session_id
            except ImportError:
                current_session_id = None
            session_id = current_session_id.get() if current_session_id else ""
            try:
                mp = await pm.start(command, cwd=self._root,
                                   session_id=session_id, port=port)
            except Exception as e:
                return {"isError": True, "error": f"启动失败：{e}"}

            result = {
                "isError": False,
                "pid": mp.pid,
                "port": port,
                "is_server": True,
                "message": f"已后台启动服务 (PID {mp.pid})"
                          + (f"，端口 {port}" if port else ""),
                "stop_command": f"taskkill /F /PID {mp.pid}" if os.name == "nt"
                                else f"kill {mp.pid}",
            }
            logger.info("background process started  pid=%d  port=%s  cmd=%s",
                       mp.pid, port, command[:80])
            return result

        # 普通模式（当前行为）
        # 自动清理命令中的冗余前缀（cwd 已是 workspace root）
        command = re.sub(r"\bcd\s+(?:/d\s+)?[\"']?(?:storage[/\\]workspace[/\\])?[\"']?\s*&&\s*", "", command)
        command = re.sub(r"\bstorage[/\\]workspace[/\\]", "", command)
        command = re.sub(r"\bstart\s+(?:/B|/MIN)\s+", "", command)
        try:
            env = os.environ.copy()
            existing = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = self._root + (os.pathsep + existing if existing else "")
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self._root,
                env=env,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self._timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)
                except asyncio.TimeoutError:
                    stdout = b""; stderr = b""
                # python xxx.py 超时 → 很可能是服务进程，切后台
                if command.strip().startswith("python ") and pm is not None:
                    logger.info("timeout → restarting as background: %s", command[:80])
                    port = None
                    m = self._PORT_RE.search(command)
                    if m:
                        port = int(m.group(1))
                    try:
                        from app.core.session_context import current_session_id
                    except ImportError:
                        current_session_id = None
                    sid = current_session_id.get() if current_session_id else ""
                    try:
                        mp = await pm.start(command, cwd=self._root,
                                           session_id=sid, port=port)
                        return {
                            "isError": False,
                            "pid": mp.pid,
                            "port": port,
                            "is_server": True,
                            "message": f"命令超时后已转为后台运行 (PID {mp.pid})"
                                      + (f"，端口 {port}" if port else ""),
                            "stop_command": f"taskkill /F /PID {mp.pid}" if os.name == "nt"
                                            else f"kill {mp.pid}",
                        }
                    except Exception as e:
                        return {
                            "isError": True,
                            "error": f"命令超时且后台启动失败：{e}  cmd={command[:80]}",
                        }
                return {
                    "isError": True,
                    "error": f"命令超时（{self._timeout}s）：{command[:80]}",
                    "pid": proc.pid,
                    "stdout": stdout.decode("utf-8", errors="replace")[:500],
                    "stderr": stderr.decode("utf-8", errors="replace")[:500],
                }
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")
            if len(stdout_str) > self._max_output:
                stdout_str = stdout_str[:self._max_output] + "\n...(输出截断)"
            if len(stderr_str) > self._max_output:
                stderr_str = stderr_str[:self._max_output] + "\n...(输出截断)"
            result = {
                "isError": proc.returncode != 0,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "returncode": proc.returncode,
            }
            # 增强错误信息
            if proc.returncode != 0 and not stderr_str.strip():
                result["error"] = f"exit={proc.returncode}  cmd={command[:100]}"
            elif proc.returncode != 0:
                result["error"] = f"exit={proc.returncode}  {stderr_str.strip()[:200]}"
            return result
        except Exception as e:
            logger.warning("run_code 异常: %s: %s  cmd=%s", type(e).__name__, e, command[:120])
            return {"isError": True, "error": f"执行失败 [{type(e).__name__}]：{e}  cmd={command[:100]}"}


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
