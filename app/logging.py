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

def log_call(*, label: str | None = None,
              fmt_entry: str = "",
              fmt_exit: str = ""):
    """装饰异步函数：入口打印参数，出口打印返回值/异常 + 耗时。

    fmt_entry / fmt_exit 使用 {key} 占位符：
      fmt_entry 可用：函数所有参数名
      fmt_exit  可用：_result（返回值）+ _elapsed（秒）
      如果 _result 是 dict，还自动注入 _result 中的 key 作为独立变量

    例：
      @log_call(label="deepseek.chat",
                fmt_entry="model={self._model} msgs={len(messages)}",
                fmt_exit="content={content_len}chars  tool_calls={tc_count}")
    """
    def deco(fn):
        name = label or fn.__name__

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            lg = logging.getLogger(fn.__module__)

            # 入口
            if fmt_entry:
                try:
                    ctx = _build_ctx(fn, args, kwargs)
                    entry_msg = fmt_entry.format(**ctx)
                except Exception:
                    entry_msg = _default_entry(fn, args, kwargs)
            else:
                entry_msg = _default_entry(fn, args, kwargs)
            lg.debug("→ %s  %s", name, entry_msg)

            t0 = time.time()
            try:
                result = await fn(*args, **kwargs)
                _elapsed = time.time() - t0
                if fmt_exit:
                    try:
                        ctx = _build_ctx(fn, args, kwargs)
                        ctx["_elapsed"] = _elapsed
                        ctx["_result"] = result
                        # 如果返回值是 dict，注入其 key 作为独立变量，方便模板直接用 {key}
                        if isinstance(result, dict):
                            ctx.update(result)
                        exit_msg = fmt_exit.format(**ctx)
                    except Exception:
                        exit_msg = _default_exit(result, _elapsed)
                else:
                    exit_msg = _default_exit(result, _elapsed)
                lg.info("← %s  %.1fs  %s", name, _elapsed, exit_msg)
                return result
            except Exception as exc:
                _elapsed = time.time() - t0
                lg.error("← %s  %.1fs  ERROR  %s: %s", name, _elapsed,
                         type(exc).__name__, str(exc)[:300])
                raise

        return wrapper
    return deco


def _build_ctx(fn, args, kwargs) -> dict:
    """构建模板上下文：{参数名: 值}。"""
    import inspect
    sig = inspect.signature(fn)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)


def _summarize_val(v, max_len: int = 80) -> str:
    """智能摘要：list/dict 显示关键信息，str 截断。"""
    if isinstance(v, (list, tuple)):
        if v and isinstance(v[0], dict):
            return f"[{len(v)} dicts]"
        return f"[{len(v)} items]"
    if isinstance(v, dict):
        # dict 优先显示关键字段
        for key in ("path", "query", "url", "name", "error", "command"):
            if key in v:
                val = str(v[key])[:max_len - len(key) - 10]
                return f"{key}={val}"
        return f"{{{len(v)} keys}}"
    if hasattr(v, "to_api_schema"):
        try:
            return f"tools={len(v.to_api_schema())}"
        except Exception:
            pass
    s = str(v)
    s = s.replace("\n", " ")
    if len(s) > max_len:
        s = s[:max_len] + "…"
    return s


def _default_entry(fn, args, kwargs) -> str:
    parts = []
    for a in args[1:]:
        parts.append(_summarize_val(a, 60))
    for k, v in kwargs.items():
        parts.append(f"{k}={_summarize_val(v, 60)}")
    return ", ".join(parts) if parts else ""


def _default_exit(result, elapsed: float) -> str:
    if isinstance(result, dict):
        reason = result.get("reason", "")
        msgs = result.get("messages")
        extra = ""
        if msgs and isinstance(msgs, list):
            extra = f" msgs={len(msgs)}"
        return f"{reason}{extra}" if reason else _summarize_val(result, 60)
    return _summarize_val(result, 60)


def log_tool(fn):
    """装饰工具 call 方法：记录 tool name / input / result / 耗时 + 错误详情。"""
    @functools.wraps(fn)
    async def wrapper(self, tool_input: dict, context: dict | None = None):
        lg = logging.getLogger(fn.__module__)
        tool_name = getattr(self, "name", type(self).__name__)
        inp = _summarize_val(tool_input, 120)
        lg.info("🔧 %s  %s", tool_name, inp)

        t0 = time.time()
        try:
            result = await fn(self, tool_input, context)
            elapsed = time.time() - t0
            if isinstance(result, dict) and result.get("isError"):
                err = result.get("error") or result.get("stderr") or "未知错误"
                lg.warning("🔧 %s  %.1fs  FAIL  %s", tool_name, elapsed,
                           str(err)[:200].replace("\n", " "))
            else:
                summary = _summarize_tool_result(tool_name, result)
                lg.info("🔧 %s  %.1fs  %s", tool_name, elapsed, summary)
            return result
        except Exception as exc:
            elapsed = time.time() - t0
            lg.error("🔧 %s  %.1fs  EXCEPTION  %s: %s", tool_name, elapsed,
                     type(exc).__name__, str(exc)[:300])
            raise

    return wrapper


def _summarize_tool_result(name: str, result: dict) -> str:
    """一行摘要工具返回结果。"""
    if not isinstance(result, dict):
        return _summarize_val(result, 80)
    if name == "search_web":
        n = len(result.get("results", []))
        filtered = result.get("filtered_count", 0)
        extra = f" filtered={filtered}" if filtered else ""
        return f"{n} results{extra}"
    if name == "read_url":
        return f"{len(result.get('content', ''))} chars"
    if name in ("file_write", "file_read"):
        return result.get("path", "?")
    if name == "run_code":
        return f"exit={result.get('returncode', '?')}"
    if name == "list_files":
        files = result.get("files", "")
        return f"{len(files)} files"
    if name == "learning_todo_write":
        return f"{result.get('count', 0)} todos"
    return _summarize_val(str(dict(list(result.items())[:1])), 60)
