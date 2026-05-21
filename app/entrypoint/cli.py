"""CLI entrypoint helpers."""

from __future__ import annotations

import argparse
import asyncio
import json

from app.config.settings import load_settings
from app.core.workflow import LearnWorkflow, create_default_storage
from app.llm.deepseek_client import DeepSeekLLMClient
from app.llm.model_selector import ModelSelector
from app.llm.mock_client import MockLLMClient
from app.memory.memory_store import MemoryStore
from app.tasks.todo_store import TodoStore
from app.tools.memory_tools import SaveMemoryTool, SearchMemoryTool
from app.tools.mock_learning_tools import (
    MockGitHubRepoAnalyzerTool,
    MockReadUrlTool,
    MockSearchWebTool,
)
from app.tools.registry import ToolRegistry
from app.tools.todo_tools import LearningTodoWriteTool


def build_default_tool_registry(
    todo_store: TodoStore | None = None,
    memory_store: MemoryStore | None = None,
) -> ToolRegistry:
    registry = ToolRegistry()
    resolved_memory_store = memory_store or MemoryStore("storage/memory")
    registry.register(MockSearchWebTool())
    registry.register(MockReadUrlTool())
    registry.register(MockGitHubRepoAnalyzerTool())
    registry.register(LearningTodoWriteTool(todo_store or TodoStore("storage/tasks")))
    registry.register(SearchMemoryTool(resolved_memory_store))
    registry.register(SaveMemoryTool(resolved_memory_store))
    return registry


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="learnagent")
    parser.add_argument("prompt", nargs="*", help="学习主题、文档链接或 GitHub 仓库地址")
    parser.add_argument("--real", action="store_true", help="使用真实 DeepSeek LLM")
    parser.add_argument("--json", action="store_true", help="输出结构化 JSON")
    parser.add_argument("--mode", default="normal", help="模型模式，例如 normal/deep/planning")
    return parser.parse_args(argv)


async def run_workflow_once(user_input: str, llm=None, mode: str | None = None):
    session_store, memory_store = create_default_storage()
    workflow = LearnWorkflow(
        llm=llm or MockLLMClient(),
        tools=build_default_tool_registry(
            todo_store=TodoStore("storage/tasks"),
            memory_store=memory_store,
        ),
        session_store=session_store,
        memory_store=memory_store,
        model_mode=mode,
    )
    return await workflow.run(user_input)


async def run_once(user_input: str, llm=None, mode: str | None = None) -> str:
    result = await run_workflow_once(user_input, llm=llm, mode=mode)
    return result.content


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    user_input = " ".join(args.prompt).strip() if args.prompt else input("LearnAgent> ").strip()
    if not user_input:
        print("请输入学习主题、文档链接或 GitHub 仓库地址。")
        return 1
    llm = _build_llm(use_real=args.real)
    result = asyncio.run(run_workflow_once(user_input, llm=llm, mode=args.mode))
    if args.json:
        print(json.dumps(_workflow_result_to_dict(result), ensure_ascii=False))
    else:
        print(result.content)
    return 0


def _build_llm(use_real: bool):
    if not use_real:
        return MockLLMClient()
    settings = load_settings()
    return DeepSeekLLMClient(
        settings=settings,
        model_selector=ModelSelector(settings),
    )


def _workflow_result_to_dict(result) -> dict:
    return {
        "intent": result.intent,
        "topic": result.topic,
        "content": result.content,
        "output": result.output.to_dict(),
        "session_id": result.session_id,
        "metadata": result.metadata,
    }
