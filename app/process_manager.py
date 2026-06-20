"""后台进程管理器 —— 管理 run_code 启动的长期服务进程。

每个进程记录 PID、启动命令、端口、运行时间、最近 N 行输出。
WebSocket 可实时推送输出流。
"""

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, List


@dataclass
class ManagedProcess:
    pid: int
    command: str
    port: int | None = None
    started_at: float = field(default_factory=time.time)
    status: str = "running"  # running | stopped | error
    output_lines: List[str] = field(default_factory=list)
    _process: asyncio.subprocess.Process | None = field(default=None, repr=False)
    _stream_task: asyncio.Task | None = field(default=None, repr=False)

    @property
    def elapsed(self) -> float:
        if self.status == "running":
            return time.time() - self.started_at
        return 0.0

    @property
    def output(self) -> str:
        return "\n".join(self.output_lines[-50:])

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "command": self.command[:100],
            "port": self.port,
            "status": self.status,
            "elapsed": round(self.elapsed, 1),
            "output": self.output,
        }


class ProcessManager:
    """全局单例，管理所有 session 的后台进程。"""

    def __init__(self, max_output_lines: int = 200):
        self._processes: Dict[int, ManagedProcess] = {}
        self._max_lines = max_output_lines
        self._output_callbacks: List[callable] = []

    def add_output_callback(self, cb):
        self._output_callbacks.append(cb)

    def remove_output_callback(self, cb):
        if cb in self._output_callbacks:
            self._output_callbacks.remove(cb)

    async def _broadcast(self, pid: int, port: int | None, line: str):
        for cb in self._output_callbacks:
            try:
                await cb(pid, port, line)
            except Exception:
                pass

    async def start(
        self,
        command: str,
        cwd: str,
        port: int | None = None,
    ) -> ManagedProcess:
        """启动后台进程，立即返回。"""
        env = os.environ.copy()
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = cwd + (os.pathsep + existing if existing else "")

        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=cwd,
            env=env,
        )

        mp = ManagedProcess(
            pid=proc.pid,
            command=command,
            port=port,
            _process=proc,
        )
        self._processes[proc.pid] = mp

        # 后台任务：逐行读取输出
        mp._stream_task = asyncio.create_task(self._read_stream(mp))

        return mp

    async def _read_stream(self, mp: ManagedProcess):
        """读取进程输出直到结束。"""
        proc = mp._process
        if proc is None or proc.stdout is None:
            return

        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip()
                mp.output_lines.append(text)
                if len(mp.output_lines) > self._max_lines:
                    mp.output_lines = mp.output_lines[-self._max_lines:]

                # 广播到所有 WebSocket
                await self._broadcast(mp.pid, mp.port, text)

            await proc.wait()
            mp.status = "stopped"
        except asyncio.CancelledError:
            pass
        except Exception:
            mp.status = "error"

    async def stop(self, pid: int) -> bool:
        """停止指定进程。"""
        mp = self._processes.get(pid)
        if mp is None or mp.status != "running":
            return False

        proc = mp._process
        if proc:
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass

        if mp._stream_task:
            mp._stream_task.cancel()

        mp.status = "stopped"
        mp._process = None
        return True

    def get(self, pid: int) -> Optional[ManagedProcess]:
        return self._processes.get(pid)

    def list_all(self) -> List[dict]:
        return [mp.to_dict() for mp in self._processes.values()
                if mp.status == "running"]

    async def stop_all(self):
        for pid in list(self._processes.keys()):
            await self.stop(pid)


# 模块级单例
_pm: Optional[ProcessManager] = None

def get_process_manager() -> Optional[ProcessManager]:
    return _pm

def set_process_manager(pm: ProcessManager) -> None:
    global _pm
    _pm = pm


def looks_like_server(command: str) -> bool:
    """检测命令是否会启动长期服务（Flask/uvicorn/node 等）。"""
    cmd = command.lower().replace(" ", "")
    keywords = [
        "app.run", "flaskrun", "uvicorn", "gunicorn",
        "npmstart", "npmrundev", "npxserve", "vite",
        "python-mhttp.server", "pythonserver.py",
        "live-server", "nodemon",
    ]
    return any(kw in cmd for kw in keywords)
