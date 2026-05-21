"""LearnAgent CLI 入口。

使用方式：
    python -m app.main              # 使用 MockLLMClient + Mock 工具（无需 API key）
    python -m app.main --real       # 使用 DeepSeek API（需要 .env 配置）
"""

import asyncio
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
from app.core.router import InputRouter
from app.core.query_engine import LearnQueryEngine, INTENT_TO_SKILL
from app.memory.session_store import SessionStore
from app.memory.memory_store import MemoryStore


def build_engine(use_real: bool = False):
    cfg = get_config()

    # 存储初始化
    storage_base = cfg.storage_base_dir
    session_store = SessionStore(base_dir=os.path.join(storage_base, "sessions"))
    memory_store = MemoryStore(base_dir=os.path.join(storage_base, "memory"))

    # 工具注册
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

    # workspace 工具（路径限制在 workspace/ 目录）
    workspace_dir = os.path.join(storage_base, "workspace")
    tools.register(FileWrite(workspace_root=workspace_dir))
    tools.register(FileRead(workspace_root=workspace_dir))
    tools.register(RunCode(workspace_root=workspace_dir, timeout=30))
    tools.register(ListFiles(workspace_root=workspace_dir))

    # LLM 客户端
    if use_real:
        from app.llm.deepseek_client import DeepSeekLLMClient

        selector = ModelSelector(cfg.small_model, cfg.large_model)
        model = selector.select(cfg.model_mode)
        llm = DeepSeekLLMClient(
            api_key=cfg.api_key or "",
            base_url=cfg.base_url,
            model=model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
    else:
        llm = MockLLMClient()

    return LearnQueryEngine(
        llm=llm,
        tools=tools,
        session_store=session_store,
        memory_store=memory_store,
        skills_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills"),
    )


async def ask_permission(tool_name: str, reason: str, tool_input: dict | None = None) -> bool:
    """CLI 交互式权限确认，显示工具参数。"""
    print(f"\n[权限] {tool_name} 请求执行")
    print(f"  原因：{reason}")
    if tool_input:
        # 显示关键参数（截断长内容）
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
    """CLI 进度事件回调：显示 LLM 思考、工具执行等中间状态。"""
    if event_type == "thinking":
        t = data.get("turn", "?")
        m = data.get("max_turns", "?")
        sys.stdout.write(f"  [{t}/{m}] 思考中...")
        sys.stdout.flush()
    elif event_type == "thought":
        if data.get("has_content"):
            n = data.get("content_len", 0)
            sys.stdout.write(f"\r  [{data['turn']}/{data['max_turns']}] LLM 回复文本 ({n} 字)       \n")
        else:
            sys.stdout.write(f"\r  [{data['turn']}/{data['max_turns']}] LLM 决定调用工具           \n")
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


def _describe_tool_call(name: str, inp: dict) -> str:
    """生成工具调用的简短描述。"""
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
        return f"列出文件"
    if name == "learning_todo_write":
        n = len(inp.get("todos", []))
        return f"保存 {n} 项学习任务"
    return f"{name}"


async def main():
    use_real = "--real" in sys.argv
    engine = build_engine(use_real=use_real)
    engine.set_ask_callback(ask_permission)
    engine.set_on_event(on_event)
    router = InputRouter()
    t_session_start = time.time()

    mode = "真实 API (DeepSeek)" if use_real else "Mock 模式"
    print(f"LearnAgent v0.1.0 | {mode}")
    print(f"已注册工具：{', '.join(engine.tools._tools.keys())}")
    print(f"会话 ID：{engine.session_id}")
    skills_loaded = [s for s in engine._skills.keys()]
    if skills_loaded:
        print(f"已加载 Skill：{', '.join(skills_loaded)}")
    print("输入 /help 查看命令，/exit 退出\n")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        # Router 识别意图
        route = router.route(user_input)
        intent = route["intent"]
        topic = route.get("topic")

        if not user_input.startswith("/"):
            skill_name = INTENT_TO_SKILL.get(intent)
            skill_info = f" skill={skill_name}" if skill_name else ""
            print(f"[Router] intent={intent} topic={topic}{skill_info}")

        result = await engine.submit_message(user_input, topic=topic, intent=intent)

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
