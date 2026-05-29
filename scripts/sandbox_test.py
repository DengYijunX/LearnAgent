"""沙箱测试脚本 —— 驱动 LearnAgent 执行预设对话，记录完整输出。

用法：
    python scripts/sandbox_test.py [--real] [--output docs/sandbox_test_001.md]

输出格式：Markdown，包含输入、输出、工具调用、耗时。
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import get_config
from app.llm.deepseek_client import DeepSeekLLMClient
from app.llm.mock_client import MockLLMClient
from app.llm.model_selector import ModelSelector
from app.tools.registry import ToolRegistry
from app.tools.search_web import RealSearchWeb, MockSearchWeb
from app.tools.read_url import RealReadUrl, MockReadUrl
from app.tools.github_analyzer import RealGitHubAnalyzer, MockGitHubAnalyzer
from app.tools.workspace_tools import FileWrite, FileRead, RunCode, ListFiles
from app.tools.todo_tools import LearningTodoWrite
from app.core.agent_loop import agent_loop
from app.core.llm_router import LLMRouter
from app.core.query_engine import LearnQueryEngine, INTENT_TO_SKILL
from app.memory.session_store import SessionStore
from app.memory.memory_store import MemoryStore
from app.context.context_builder import build_system_prompt
from app.skills.loader import load_skill


class LogRecorder:
    """记录所有交互输出到 Markdown 格式。"""
    def __init__(self, output_path: str):
        self._f = open(output_path, "w", encoding="utf-8")
        self._f.write("# LearnAgent 沙箱测试记录\n\n")
        self._f.write(f"**时间：** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        self._f.write(f"**模型：** {get_config().small_model}\n\n")
        self._f.write("---\n\n")

    def section(self, title: str):
        self._f.write(f"\n## {title}\n\n")

    def user_input(self, text: str):
        self._f.write(f"**用户输入：** {text}\n\n")
        sys.stdout.write(f"\n> {text}\n")
        sys.stdout.flush()

    def system_output(self, text: str):
        self._f.write(f"**系统输出：**\n\n{text}\n\n---\n")
        sys.stdout.write(f"\n{text}\n\n")
        sys.stdout.flush()

    def tool_call(self, name: str, summary: str, elapsed: float, is_err: bool = False):
        icon = "❌" if is_err else "✅"
        line = f"  {icon} {summary} ({elapsed:.1f}s)"
        self._f.write(f"{line}\n\n")
        sys.stdout.write(f"{line}\n")
        sys.stdout.flush()

    def tool_summary(self, counts: dict, elapsed: float):
        parts = " · ".join(f"{k} ×{v}" for k, v in sorted(counts.items()))
        line = f"\n  ⏱ {elapsed:.0f}s · {parts}"
        self._f.write(f"{line}\n\n")
        sys.stdout.write(f"{line}\n")
        sys.stdout.flush()

    def close(self):
        self._f.close()


async def run_sandbox_test(use_real: bool = False, output_path: str = "docs/sandbox_test_001.md"):
    cfg = get_config()
    log = LogRecorder(output_path)
    storage_base = cfg.storage_base_dir

    # 清理测试 workspace
    test_ws = os.path.join(storage_base, "workspace", "_sandbox_test")
    if os.path.exists(test_ws):
        import shutil
        shutil.rmtree(test_ws, ignore_errors=True)
    os.makedirs(test_ws, exist_ok=True)

    # 构建引擎
    tools = ToolRegistry()
    if use_real:
        tools.register(RealSearchWeb(max_results=5))
        tools.register(RealReadUrl(timeout=15))
        tools.register(RealGitHubAnalyzer(timeout=20))
        from app.llm.deepseek_client import DeepSeekLLMClient
        selector = ModelSelector(cfg.small_model, cfg.large_model)
        llm = DeepSeekLLMClient(
            api_key=cfg.api_key or "",
            base_url=cfg.base_url,
            model=selector.select(cfg.model_mode),
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
        router = LLMRouter(llm)
    else:
        tools.register(MockSearchWeb())
        tools.register(MockReadUrl())
        tools.register(MockGitHubAnalyzer())
        llm = MockLLMClient()
        router = None

    tools.register(LearningTodoWrite())
    tools.register(FileWrite(workspace_root=test_ws))
    tools.register(FileRead(workspace_root=test_ws))
    tools.register(RunCode(workspace_root=test_ws, timeout=10))
    tools.register(ListFiles(workspace_root=test_ws))

    # 加载 Skills
    skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")
    skills_map = {}
    for name in ("learn-concept", "read-repo", "review-progress"):
        s = load_skill(os.path.join(skills_dir, name))
        if s:
            skills_map[name] = s["body"]

    log.section("测试会话开始")

    # 测试用例
    test_cases = [
        {
            "input": "介绍一下 Python 装饰器的核心概念，写一个简单例子",
            "expected_intent": "learn_concept",
        },
        {
            "input": "装饰器在实际项目中有什么应用场景",
            "expected_intent": "learn_concept",
        },
    ]

    messages = []
    topic = None

    for i, case in enumerate(test_cases, 1):
        user_input = case["input"]

        # LLM Router
        if router:
            sys.stdout.write("  分析意图...")
            sys.stdout.flush()
            route = await router.route(user_input)
            intent = route["intent"]
            new_topic = route.get("topic")
            sys.stdout.write(f"\r  意图: {intent} · 主题: {new_topic or '无'}\n")
            sys.stdout.flush()
        else:
            intent = "learn_concept"
            new_topic = None

        if new_topic:
            topic = new_topic

        log.user_input(user_input)

        # 构建 system prompt
        skill_body = skills_map.get(INTENT_TO_SKILL.get(intent, ""))
        system = build_system_prompt(
            current_topic=topic,
            intent=intent,
            skill_body=skill_body,
        )
        messages.append({"role": "user", "content": user_input})

        # 事件回调
        tool_counts = {}

        async def on_event(event_type, data):
            if event_type == "thinking":
                sys.stdout.write("  ...")
                sys.stdout.flush()
            elif event_type == "thought":
                sys.stdout.write("\r" + " " * 40 + "\r")
                sys.stdout.flush()
            elif event_type == "tool_start":
                name = data["name"]
                inp = data.get("input", {})
                if name == "search_web":
                    desc = f"搜索: {inp.get('query', '')[:40]}"
                elif name == "file_write":
                    desc = f"写文件: {inp.get('path', '?')}"
                elif name == "run_code":
                    desc = f"执行: {inp.get('command', '')[:40]}"
                else:
                    desc = name
                sys.stdout.write(f"  >> {desc}...")
                sys.stdout.flush()
            elif event_type == "tool_end":
                elapsed = data.get("elapsed", 0)
                summary = data.get("result_summary", "")
                is_err = data.get("is_error", False)
                name = data.get("name", "")
                tool_counts[name] = tool_counts.get(name, 0) + 1
                log.tool_call(name, summary, elapsed, is_err)

        # 运行 Agent Loop
        t0 = time.time()
        result = await agent_loop(
            messages=messages,
            llm=llm,
            tools=tools,
            system=system,
            max_turns=8,
            on_event=on_event,
        )

        # 提取最终文本
        final_text = None
        for m in reversed(result["messages"]):
            if m.get("role") == "assistant" and m.get("content"):
                final_text = m["content"]
                break

        elapsed = time.time() - t0
        log.tool_summary(tool_counts, elapsed)

        if final_text:
            # 截断过长输出
            display = final_text[:1500]
            if len(final_text) > 1500:
                display += f"\n\n...(共 {len(final_text)} 字，已截断)"
            log.system_output(display)

    # 检查 workspace 文件
    log.section("Workspace 生成文件")
    for root, dirs, files in os.walk(test_ws):
        for f in files:
            p = os.path.join(root, f)
            size = os.path.getsize(p)
            log._f.write(f"- `{os.path.relpath(p, test_ws)}` ({size} 字节)\n")

    log.close()
    print(f"\n测试记录已保存至：{output_path}")


if __name__ == "__main__":
    use_real = "--real" in sys.argv
    output_path = "docs/sandbox_test_001.md"
    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]

    asyncio.run(run_sandbox_test(use_real=use_real, output_path=output_path))
