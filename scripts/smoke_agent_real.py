"""Manual smoke test for real DeepSeek LLM with mock LearnAgent tools."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.config.settings import load_settings
from app.core.workflow import LearnWorkflow, create_default_storage
from app.entrypoint.cli import build_default_tool_registry
from app.llm.deepseek_client import DeepSeekLLMClient
from app.llm.model_selector import ModelSelector


async def main() -> int:
    settings = load_settings()
    if not settings.run_real_tests and os.getenv("RUN_REAL_TESTS") != "1":
        print("跳过真实 Agent smoke test：请设置 RUN_REAL_TESTS=1。")
        return 0

    session_store, memory_store = create_default_storage()
    llm = DeepSeekLLMClient(
        settings=settings,
        model_selector=ModelSelector(settings),
    )
    workflow = LearnWorkflow(
        llm=llm,
        tools=build_default_tool_registry(),
        session_store=session_store,
        memory_store=memory_store,
    )
    result = await workflow.run("我想学习 LangGraph，请给一个第一阶段学习路线。")
    if not result.content.strip():
        print(f"真实 Agent smoke test 未得到最终文本输出：{result.metadata}")
        return 1
    print(result.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
