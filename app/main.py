"""LearnAgent CLI 入口。

使用方式：
    python -m app.main              # 新建会话（Mock 模式）
    python -m app.main --real       # 新建会话（DeepSeek API）
    python -m app.main --resume <id>          # 恢复指定会话
    python -m app.main --resume latest        # 恢复最近会话
    python -m app.main --real --resume latest # 真实模式 + 恢复最近会话
"""

import asyncio
import glob
import json
import os
import sys
import time

from app.config.settings import get_config
from app.llm.mock_client import MockLLMClient
from app.llm.model_selector import ModelSelector
from app.tools.registry import ToolRegistry
from app.tools.search_web import MockSearchWeb, RealSearchWeb
from app.tools.read_url import MockReadUrl, RealReadUrl
from app.tools.github_analyzer import MockGitHubAnalyzer, RealGitHubAnalyzer
from app.tools.workspace_tools import FileWrite, FileRead, RunCode, ListFiles
from app.tools.todo_tools import LearningTodoWrite
from app.core.router import InputRouter, normalize_topic
from app.core.query_engine import LearnQueryEngine, INTENT_TO_SKILL
from app.memory.session_store import SessionStore
from app.memory.memory_store import MemoryStore


def _get_workspace_dir(storage_base: str, topic: str | None) -> str:
    """根据 topic 返回 workspace 路径。无 topic 时用 _default。"""
    name = topic or "_default"
    return os.path.join(storage_base, "workspace", name)


def _register_workspace_tools(tools: ToolRegistry, workspace_dir: str):
    """(Re)register workspace tools for a given workspace directory."""
    # 移除旧的 workspace 工具
    for name in ("file_write", "file_read", "run_code", "list_files"):
        if tools.find(name):
            del tools._tools[name]
    # 注册新的
    os.makedirs(workspace_dir, exist_ok=True)
    tools.register(FileWrite(workspace_root=workspace_dir))
    tools.register(FileRead(workspace_root=workspace_dir))
    tools.register(RunCode(workspace_root=workspace_dir, timeout=30))
    tools.register(ListFiles(workspace_root=workspace_dir))


def build_engine(use_real: bool = False, resume_id: str | None = None):
    cfg = get_config()
    storage_base = cfg.storage_base_dir
    session_store = SessionStore(base_dir=os.path.join(storage_base, "sessions"))
    memory_store = MemoryStore(base_dir=os.path.join(storage_base, "memory"))

    # 工具注册（workspace 工具根据 topic 动态注册）
    tools = ToolRegistry()
    if use_real:
        tools.register(RealSearchWeb(max_results=5))
        tools.register(RealReadUrl(timeout=15))
        tools.register(RealGitHubAnalyzer(timeout=20))
    else:
        tools.register(MockSearchWeb())
        tools.register(MockReadUrl())
        tools.register(MockGitHubAnalyzer())
    tools.register(LearningTodoWrite())

    # workspace 工具：初始默认目录
    _register_workspace_tools(tools, _get_workspace_dir(storage_base, None))

    # LLM
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

    # Session 恢复
    if resume_id:
        _resume_session(engine, session_store, storage_base, resume_id)

    return engine


def _resume_session(engine, session_store, storage_base, resume_id: str):
    """从 JSONL 恢复会话消息和 topic。"""
    if resume_id == "latest":
        base = session_store._base_dir
        files = sorted(glob.glob(os.path.join(base, "*.jsonl")), key=os.path.getmtime, reverse=True)
        if not files:
            print("[Session] 暂无历史会话，已新建。")
            return
        resume_id = os.path.splitext(os.path.basename(files[0]))[0]

    msgs = session_store.get_messages(resume_id)
    if not msgs:
        print(f"[Session] 会话 {resume_id} 为空，已新建。")
        return

    engine.messages = msgs
    engine.session_id = resume_id
    engine.started_at = os.path.getmtime(session_store._path(resume_id))

    # 尝试从 memory 恢复 topic
    records = engine.memory_store.list_by_type("learning") if engine.memory_store else []
    if records:
        last = records[-1]
        engine.current_topic = last.get("name", "").replace("topic_", "")

    print(f"[Session] 已恢复会话 {resume_id[:12]}，{len(msgs)} 条消息")
    if engine.current_topic:
        print(f"[Session] 上一次主题：{engine.current_topic}")


async def ask_permission(tool_name: str, reason: str, tool_input: dict | None = None) -> bool:
    print(f"\n[权限] {tool_name} 请求执行")
    print(f"  原因：{reason}")
    if tool_input:
        for k, v in tool_input.items():
            v_str = str(v)
            if len(v_str) > 80:
                v_str = v_str[:80] + "..."
            print(f"  {k}: {v_str}")
    try:
        answer = input("  允许？(y/n，默认 y): ").strip().lower()
        return answer in ("y", "yes", "")
    except (EOFError, KeyboardInterrupt):
        return False


async def on_event(event_type: str, data: dict):
    if event_type == "thinking":
        t = data.get("turn", "?")
        m = data.get("max_turns", "?")
        sys.stdout.write(f"  [{t}/{m}] 思考中...")
        sys.stdout.flush()
    elif event_type == "thought":
        t = data.get("turn", "?")
        m = data.get("max_turns", "?")
        if data.get("has_content"):
            n = data.get("content_len", 0)
            sys.stdout.write(f"\r  [{t}/{m}] LLM 回复文本 ({n} 字)       \n")
        else:
            sys.stdout.write(f"\r  [{t}/{m}] LLM 决定调用工具           \n")
        sys.stdout.flush()
    elif event_type == "tool_start":
        name = data["name"]
        inp = data.get("input", {})
        desc = _describe_tool_call(name, inp)
        sys.stdout.write(f"     ⚙ {desc}...")
        sys.stdout.flush()
    elif event_type == "tool_end":
        elapsed = data.get("elapsed", 0)
        summary = data.get("result_summary", "")
        is_err = data.get("is_error", False)
        status = "✗" if is_err else "✓"
        sys.stdout.write(f"\r     {status} {summary} ({elapsed:.1f}s)     \n")
        sys.stdout.flush()
    elif event_type == "topic_change":
        msg = data.get("message", "")
        new_topic = data.get("new_topic", "")
        print(f"\n  📁 {msg}")
        # workspace 切换提示
        storage = os.path.join(get_config().storage_base_dir, "workspace", new_topic or "_default")
        print(f"  📂 workspace: {storage}")


def _describe_tool_call(name: str, inp: dict) -> str:
    if name == "search_web":
        return f"搜索：{inp.get('query', '')[:60]}"
    if name == "read_url":
        return f"读取：{inp.get('url', '')[:60]}"
    if name == "analyze_github_repo":
        return f"分析仓库：{inp.get('repo_url', '')[:60]}"
    if name == "file_write":
        return f"写文件：{inp.get('path', '?')}"
    if name == "file_read":
        return f"读文件：{inp.get('path', '?')}"
    if name == "run_code":
        return f"执行：{inp.get('command', '')[:60]}"
    if name == "list_files":
        return "列出文件"
    if name == "learning_todo_write":
        n = len(inp.get("todos", []))
        return f"保存 {n} 项学习任务"
    return f"{name}"


async def main():
    use_real = "--real" in sys.argv
    resume_id = None
    if "--resume" in sys.argv:
        idx = sys.argv.index("--resume")
        if idx + 1 < len(sys.argv):
            resume_id = sys.argv[idx + 1]

    engine = build_engine(use_real=use_real, resume_id=resume_id)
    engine.set_ask_callback(ask_permission)
    engine.set_on_event(on_event)
    router = InputRouter()

    mode = "真实 API (DeepSeek)" if use_real else "Mock 模式"
    print(f"LearnAgent v0.2.0 | {mode}")
    print(f"已注册工具：{', '.join(engine.tools._tools.keys())}")
    print(f"会话 ID：{engine.session_id[:12]}")
    skills_loaded = [s for s in engine._skills.keys()]
    if skills_loaded:
        print(f"已加载 Skill：{', '.join(skills_loaded)}")
    if engine.current_topic:
        print(f"当前主题：{engine.current_topic}")
    print("输入 /help 查看命令，/exit 退出\n")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        route = router.route(user_input)
        intent = route["intent"]
        topic = route.get("topic")

        if not user_input.startswith("/"):
            skill_name = INTENT_TO_SKILL.get(intent)
            skill_info = f" skill={skill_name}" if skill_name else ""
            print(f"[Router] intent={intent} topic={topic}{skill_info}")

        result = await engine.submit_message(user_input, topic=topic, intent=intent)

        # topic 切换时同步更新 workspace 工具
        if result.get("topic_change"):
            ws_dir = _get_workspace_dir(get_config().storage_base_dir, engine.current_topic)
            _register_workspace_tools(engine.tools, ws_dir)

        if result.get("type") == "command":
            msg = result.get("content", "")
            print(msg)
            if user_input.startswith("/exit"):
                break
        else:
            messages = result.get("messages", [])
            last = messages[-1] if messages else {}
            content = last.get("content", "(无输出)")
            print(f"\n{content}\n")


if __name__ == "__main__":
    asyncio.run(main())
