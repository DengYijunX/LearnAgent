"""统一日志配置 —— CLI 和 Web 共用。

用法：在入口文件最开头调用 setup_logging() 一次即可。
之后各模块用 logging.getLogger(__name__) 获取 logger。

日志同时输出到：
  - 控制台（INFO 级别）
  - 文件 logs/learnagent.log（DEBUG 级别，按天轮转）

装饰器：
  @log_call  — 异步函数入口/出口日志 + 耗时
  @log_tool  — 工具调用日志（name / input / result / 耗时）
"""

import functools
import logging
import os
import sys
import time
from logging.handlers import TimedRotatingFileHandler

_configured = False

LOG_FORMAT = "%(asctime)s  %(levelname)-7s  [%(name)s]  %(message)s"
DATE_FORMAT = "%m-%d %H:%M:%S"


# ── setup ──────────────────────────────────────────────────────────────

def setup_logging(*, level: int = logging.INFO, log_dir: str = "logs") -> None:
    """配置全局日志（幂等：多次调用只有第一次生效）。"""
    global _configured
    if _configured:
        return
    _configured = True

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(level)
    console.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(console)

    try:
        os.makedirs(log_dir, exist_ok=True)
        file_handler = TimedRotatingFileHandler(
            os.path.join(log_dir, "learnagent.log"),
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root.addHandler(file_handler)
    except OSError:
        pass


# ── decorators ─────────────────────────────────────────────────────────

def _summarize_arg(v, max_len: int = 80) -> str:
    """精简打印参数值。"""
    s = str(v)
    if len(s) > max_len:
        s = s[:max_len] + "…"
    return s.replace("\n", " ")


def log_call(*, label: str | None = None):
    """装饰异步函数：入口打印参数，出口打印返回值/异常 + 耗时。

    @log_call(label="agent_loop")
    async def agent_loop(messages, llm, tools, ...):
        ...
    """
    def deco(fn):
        name = label or fn.__name__

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            lg = logging.getLogger(fn.__module__)
            # 入口：参数摘要
            arg_parts = []
            for a in args[1:]:  # skip self
                arg_parts.append(_summarize_arg(a, 60))
            for k, v in kwargs.items():
                arg_parts.append(f"{k}={_summarize_arg(v, 60)}")
            lg.debug("→ %s(%s)", name, ", ".join(arg_parts) if arg_parts else "")

            t0 = time.time()
            try:
                result = await fn(*args, **kwargs)
                elapsed = time.time() - t0
                # 出口：返回值摘要
                if isinstance(result, dict):
                    summary = result.get("reason") or ", ".join(
                        f"{k}={_summarize_arg(v, 40)}" for k, v in list(result.items())[:3]
                    )
                else:
                    summary = _summarize_arg(result, 60)
                lg.info("← %s  %.1fs  %s", name, elapsed, summary)
                return result
            except Exception as exc:
                elapsed = time.time() - t0
                lg.error("← %s  %.1fs  ERROR %s: %s", name, elapsed,
                         type(exc).__name__, str(exc)[:200])
                raise

        return wrapper
    return deco


def log_tool(fn):
    """装饰工具 call 方法：记录 tool name / input / result / 耗时。"""
    @functools.wraps(fn)
    async def wrapper(self, tool_input: dict, context: dict | None = None):
        lg = logging.getLogger(fn.__module__)
        tool_name = getattr(self, "name", type(self).__name__)
        inp = _summarize_arg(tool_input, 80)
        lg.info("🔧 %s  input=%s", tool_name, inp)

        t0 = time.time()
        try:
            result = await fn(self, tool_input, context)
            elapsed = time.time() - t0
            is_err = result.get("isError") if isinstance(result, dict) else False
            level = lg.warning if is_err else lg.info
            level("🔧 %s  %.1fs  %s", tool_name, elapsed,
                  "error" if is_err else "ok")
            return result
        except Exception as exc:
            elapsed = time.time() - t0
            lg.error("🔧 %s  %.1fs  EXCEPTION %s: %s", tool_name, elapsed,
                     type(exc).__name__, str(exc)[:200])
            raise

    return wrapper
