"""LearnAgent CLI 入口。

使用方式：
    python -m app.main                      # 新建会话（Mock 模式）
    python -m app.main --real               # 新建会话（DeepSeek API）
    python -m app.main --real --resume <id> # 恢复会话
"""

import asyncio
import glob
import logging
import os
import sys
import time

from app.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

try:
    import msvcrt  # Windows only
except ImportError:
    msvcrt = None

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from app.config.settings import get_config
from app.llm.mock_client import MockLLMClient
from app.llm.model_selector import ModelSelector
from app.tools.registry import ToolRegistry
from app.tools.search_web import MockSearchWeb, RealSearchWeb
from app.tools.read_url import MockReadUrl, RealReadUrl
from app.tools.github_analyzer import MockGitHubAnalyzer, RealGitHubAnalyzer
from app.tools.workspace_tools import FileWrite, FileRead, RunCode, ListFiles
from app.tools.todo_tools import LearningTodoWrite
from app.core.llm_router import LLMRouter
from app.core.query_engine import LearnQueryEngine, INTENT_TO_SKILL
from app.memory.session_store import SessionStore
from app.memory.memory_store import MemoryStore
from app.mcp.loader import load_mcp_tools
from app.core.router import normalize_topic


def _get_workspace_dir(storage_base: str, topic: str | None) -> str:
    name = topic or "_default"
    return os.path.join(storage_base, "workspace", name)


def _register_workspace_tools(tools: ToolRegistry, workspace_dir: str):
    for name in ("file_write", "file_read", "run_code", "list_files"):
        if tools.find(name):
            del tools._tools[name]
    workspace_dir = os.path.abspath(workspace_dir)
    os.makedirs(workspace_dir, exist_ok=True)
    tools.register(FileWrite(workspace_root=workspace_dir))
    tools.register(FileRead(workspace_root=workspace_dir))
    tools.register(RunCode(workspace_root=workspace_dir, timeout=30))
    tools.register(ListFiles(workspace_root=workspace_dir))


def _sync_workspace_tools_for_route(
    tools: ToolRegistry,
    storage_base: str,
    topic: str | None,
    intent: str | None,
) -> str | None:
    normalized_topic = normalize_topic(topic)
    if not normalized_topic or intent == "chat":
        return None
    workspace_dir = _get_workspace_dir(storage_base, normalized_topic)
    _register_workspace_tools(tools, workspace_dir)
    return workspace_dir


async def build_engine(use_real: bool = False, resume_id: str | None = None):
    cfg = get_config()
    storage_base = cfg.storage_base_dir
    session_store = SessionStore(base_dir=os.path.join(storage_base, "sessions"))
    memory_store = MemoryStore(base_dir=os.path.join(storage_base, "memory"))

    tools = ToolRegistry()
    if use_real:
        tools.register(RealSearchWeb(max_results=5))
        tools.register(RealReadUrl(timeout=30))
        tools.register(RealGitHubAnalyzer(timeout=20))
    else:
        tools.register(MockSearchWeb())
        tools.register(MockReadUrl())
        tools.register(MockGitHubAnalyzer())
    tools.register(LearningTodoWrite())
    _register_workspace_tools(tools, _get_workspace_dir(storage_base, None))

    # MCP 工具加载
    mcp_servers = await load_mcp_tools(tools)

    if use_real:
        from app.llm.deepseek_client import DeepSeekLLMClient
        selector = ModelSelector(cfg.small_model, cfg.large_model)
        llm = DeepSeekLLMClient(
            api_key=cfg.api_key or "",
            base_url=cfg.base_url,
            model=selector.select(cfg.model_mode),
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
    else:
        llm = MockLLMClient()

    engine = LearnQueryEngine(
        llm=llm,
        tools=tools,
        session_store=session_store,
        memory_store=memory_store,
        skills_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills"),
    )

    if resume_id:
        _resume_session(engine, session_store, storage_base, resume_id)

    return engine


def _resume_session(engine, session_store, storage_base, resume_id: str):
    if resume_id == "latest":
        base = session_store._base_dir
        files = sorted(glob.glob(os.path.join(base, "*.jsonl")), key=os.path.getmtime, reverse=True)
        if not files:
            print("  暂无历史会话，已新建。")
            return
        resume_id = os.path.splitext(os.path.basename(files[0]))[0]
    msgs = session_store.get_messages(resume_id)
    if not msgs:
        print(f"  会话 {resume_id[:12]} 为空，已新建。")
        return
    engine.messages = msgs
    engine.session_id = resume_id
    records = engine.memory_store.list_by_type("learning") if engine.memory_store else []
    if records:
        engine.current_topic = records[-1].get("name", "").replace("topic_", "")
    print(f"  已恢复会话 {resume_id[:12]} ({len(msgs)} 条消息)")
    if engine.current_topic:
        print(f"  上一次主题：{engine.current_topic}")


async def ask_permission(tool_name: str, reason: str, tool_input: dict | None = None) -> bool:
    """每次写操作都需要用户确认，不设免确认窗口。"""
    name_cn = {"file_write": "写入文件", "run_code": "执行代码", "learning_todo_write": "保存学习任务"}.get(tool_name, tool_name)
    print(f"\n  ⚠ {name_cn}")
    if tool_input:
        for k, v in tool_input.items():
            print(f"     {k}: {_format_permission_value(k, v)}")
    try:
        answer = input("     允许？(y/n): ").strip().lower()
        return answer in ("y", "yes", "")
    except (EOFError, KeyboardInterrupt):
        return False


def _format_permission_value(key: str, value) -> str:
    text = str(value)
    if key == "command":
        return text
    if key == "content" and len(text) > 160:
        return f"[{len(text)} 字符] {text[:80]} ... {text[-40:]}"
    if key == "todos" and isinstance(value, list):
        preview = "; ".join(str(item.get("content", item)) for item in value[:3])
        suffix = f" ... 共 {len(value)} 项" if len(value) > 3 else ""
        return preview + suffix
    if len(text) > 160:
        return f"{text[:120]} ... {text[-30:]}"
    return text


async def on_event(event_type: str, data: dict):
    if event_type == "thinking":
        sys.stdout.write("  ⏳ 思考中...")
        sys.stdout.flush()
    elif event_type == "thought":
        if data.get("has_content"):
            sys.stdout.write("\r  ✅ 已生成回复" + " " * 20 + "\n")
        else:
            sys.stdout.write("\r  💭 分析中..." + " " * 10)
        sys.stdout.flush()
    elif event_type == "tool_start":
        name = data["name"]
        inp = data.get("input", {})
        desc = _describe_tool_call(name, inp)
        sys.stdout.write(f"\r  ⏳ {desc}..." + " " * 20)
        sys.stdout.flush()
    elif event_type == "tool_end":
        elapsed = data.get("elapsed", 0)
        summary = data.get("result_summary", "")
        is_err = data.get("is_error", False)
        icon = "❌" if is_err else "✅"
        sys.stdout.write(f"\r  {icon} {summary} ({elapsed:.1f}s)" + " " * 20 + "\n")
        sys.stdout.flush()
        # 搜索结果额外展示标题
        if data.get("name") == "search_web" and not is_err:
            titles = data.get("result_titles", [])
            for t in titles[:3]:
                sys.stdout.write(f"     · {t[:80]}\n")
            sys.stdout.flush()
    elif event_type == "topic_change":
        msg = data.get("message", "")
        new_topic = data.get("new_topic", "")
        storage = os.path.dirname(os.path.abspath(get_config().storage_base_dir))
        sys.stdout.write(f"\n  📁 {msg}\n  📂 workspace: {storage}\n")
        sys.stdout.flush()


def _describe_tool_call(name: str, inp: dict) -> str:
    if name == "search_web":
        return f"搜索「{inp.get('query', '')[:50]}」"
    if name == "read_url":
        return f"阅读网页"
    if name == "analyze_github_repo":
        return f"分析 GitHub 仓库"
    if name == "file_write":
        return f"创建文件 {inp.get('path', '?')}"
    if name == "file_read":
        return f"读取文件 {inp.get('path', '?')}"
    if name == "run_code":
        return f"运行 {inp.get('command', '')[:50]}"
    if name == "list_files":
        return "列出项目文件"
    if name == "learning_todo_write":
        return f"记录 {len(inp.get('todos', []))} 项学习任务"
    return name


TOOL_COUNT_NAMES = {
    "search_web": "搜索", "read_url": "阅读", "analyze_github_repo": "仓库分析",
    "file_write": "创建文件", "file_read": "读文件", "run_code": "运行代码",
    "list_files": "列文件", "learning_todo_write": "任务记录",
}


def _show_summary(messages: list[dict], session_id: str, elapsed: float):
    """每轮结束后显示工具统计和会话信息。"""
    counts = {}
    for m in messages:
        if m.get("role") == "tool":
            try:
                content = m.get("content", "")
                if isinstance(content, str):
                    # try to infer tool name from surrounding context is fragile
                    pass
            except Exception:
                pass
    # count tool_call messages instead
    for m in messages:
        for tc in m.get("tool_calls", []):
            fn = tc.get("function", {}).get("name", "unknown")
            counts[fn] = counts.get(fn, 0) + 1

    if not counts:
        return
    parts = []
    for fn, cnt in sorted(counts.items()):
        label = TOOL_COUNT_NAMES.get(fn, fn)
        parts.append(f"{label} ×{cnt}")
    line = " · ".join(parts)
    sys.stdout.write(f"  ── {line}  |  ⏱ {elapsed:.0f}s  |  session {session_id[:8]}\n")
    sys.stdout.flush()


def _collect_text(messages: list[dict]) -> str | None:
    """收集所有 assistant 且有 content 的消息，合并输出。"""
    parts = []
    for m in messages:
        if m.get("role") == "assistant" and m.get("content"):
            content = m["content"].strip()
            if content:
                parts.append(content)
    if parts:
        return "\n\n---\n\n".join(parts)
    return None


def _maybe_merge_pasted_lines(first_line: str) -> str:
    """检测 stdin 缓冲区是否有粘贴的剩余行，有则拼接为一条消息。"""
    if msvcrt is None:
        return first_line  # 非 Windows，不做检测
    try:
        extra_lines = []
        while msvcrt.kbhit():
            extra = input()
            if extra.strip():
                extra_lines.append(extra.strip())
        if extra_lines:
            merged = first_line + "\n" + "\n".join(extra_lines)
            print(f"  (已合并 {len(extra_lines) + 1} 行输入)")
            return merged
    except Exception:
        pass
    return first_line


# 使用 prompt_toolkit 独立历史，y/n 权限确认不会混入，且跨会话持久化
try:
    _main_session = PromptSession(history=FileHistory(os.path.expanduser("~/.learnagent_history")))
except Exception:
    _main_session = None  # 非 Windows 控制台环境（如 Git Bash、CI）回退到 input()


async def main():
    use_real = "--real" in sys.argv
    resume_id = None
    if "--resume" in sys.argv:
        idx = sys.argv.index("--resume")
        if idx + 1 < len(sys.argv):
            resume_id = sys.argv[idx + 1]

    engine = await build_engine(use_real=use_real, resume_id=resume_id)
    engine.set_ask_callback(ask_permission)
    engine.set_on_event(on_event)

    # 初始化进程管理器（CLI 和 Web 共用）
    try:
        from app.process_manager import ProcessManager, set_process_manager
        set_process_manager(ProcessManager())
    except ImportError:
        pass

    # LLM 路由器（替换正则 Router）
    router = LLMRouter(engine.llm) if use_real else None

    # 简洁启动信息
    print(f"LearnAgent v0.2.0")
    if resume_id:
        print(f"  session: {engine.session_id[:12]}")
    print(f"  输入问题开始学习 · /help 查看命令\n")

    _ctrl_c_time = 0.0

    while True:
        try:
            if _main_session is not None:
                user_input = (await _main_session.prompt_async("> ")).strip()
            else:
                user_input = input("> ").strip()
        except KeyboardInterrupt:
            now = time.time()
            if _ctrl_c_time > 0 and now - _ctrl_c_time < 2:
                print("\n再见！")
                break
            _ctrl_c_time = now
            sys.stdout.write("\r  \x1b[90m(再按一次 Ctrl+C 退出)\x1b[0m\n")
            sys.stdout.flush()
            continue
        except EOFError:
            print("\n再见！")
            break

        _ctrl_c_time = 0.0  # 正常输入后重置

        if not user_input:
            continue

        # 多行粘贴检测：Windows 下用 msvcrt.kbhit()
        user_input = _maybe_merge_pasted_lines(user_input)

        logger.info("[cli] user_input: %s", user_input[:120])

        # 命令处理
        if user_input.startswith("/"):
            if user_input == "/status":
                names = [t for t in engine.tools._tools.keys()]
                skills = [s for s in engine._skills.keys()]
                print(f"  模型: {engine.llm.__class__.__name__}")
                print(f"  会话: {engine.session_id[:12]}")
                print(f"  主题: {engine.current_topic or '无'}")
                print(f"  工具: {', '.join(names)}")
                print(f"  Skill: {', '.join(skills)}")
                continue
            result = await engine.submit_message(user_input)
            if result.get("type") == "command":
                print(result.get("content", ""))
                if user_input.startswith("/exit"):
                    break
            continue

        # LLM 路由
        if router:
            t0 = time.time()
            sys.stdout.write("  💭 分析意图...")
            sys.stdout.flush()
            user_input_sanitized = user_input.encode("utf-8", errors="surrogateescape").decode("utf-8", errors="replace")
            route = await router.route(user_input_sanitized)
            intent = route["intent"]
            topic = route.get("topic")
            elapsed = time.time() - t0
            plan_tag = " [plan]" if engine.permission_mode == "plan" else ""
            sys.stdout.write(f"\r  意图: {intent} · 主题: {topic or '无'}{plan_tag}  ({elapsed:.1f}s)\n")
            sys.stdout.flush()
        else:
            from app.core.router import InputRouter
            rr = InputRouter()
            route = rr.route(user_input)
            intent = route["intent"]
            topic = route.get("topic")

        # 提交到 QueryEngine
        t_round = time.time()
        try:
            _sync_workspace_tools_for_route(
                tools=engine.tools,
                storage_base=get_config().storage_base_dir,
                topic=topic,
                intent=intent,
            )
            result = await engine.submit_message(user_input, topic=topic, intent=intent)
        except asyncio.CancelledError:
            print("\n  操作已取消。")
            continue
        except Exception:
            print("\n  操作中断，请重试。")
            continue

        # topic 切换
        if result.get("topic_change"):
            ws_dir = _get_workspace_dir(get_config().storage_base_dir, engine.current_topic)
            _register_workspace_tools(engine.tools, ws_dir)

        # 收集本轮新产生的 assistant 文本回复
        messages = result.get("messages", [])
        start = result.get("_msg_start", 0)
        content = _collect_text(messages[start:])
        if content:
            try:
                print(f"\n{content}\n")
            except UnicodeEncodeError:
                # Windows GBK 终端无法输出 emoji，用 buffer 绕过编码层
                sys.stdout.buffer.write(f"\n{content}\n\n".encode("utf-8"))
        elif result.get("reason") == "max_searches":
            # 搜索次数用尽后 LLM 可能未输出文字，尝试取最后一条 assistant 内容
            for m in reversed(messages[start:]):
                if m.get("role") == "assistant" and m.get("content", "").strip():
                    fallback = m["content"].strip()
                    try:
                        print(f"\n{fallback}\n")
                    except UnicodeEncodeError:
                        sys.stdout.buffer.write(f"\n{fallback}\n\n".encode("utf-8"))
                    break

        # 收尾栏
        elapsed = time.time() - t_round
        _show_summary(result.get("messages", []), engine.session_id, elapsed)


if __name__ == "__main__":
    asyncio.run(main())
