"""CLI entrypoint helpers."""

from __future__ import annotations

import asyncio

from app.core.workflow import LearnWorkflow, create_default_storage
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


async def run_once(user_input: str) -> str:
    session_store, memory_store = create_default_storage()
    workflow = LearnWorkflow(
        llm=MockLLMClient(),
        tools=build_default_tool_registry(
            todo_store=TodoStore("storage/tasks"),
            memory_store=memory_store,
        ),
        session_store=session_store,
        memory_store=memory_store,
    )
    result = await workflow.run(user_input)
    return result.content


def main() -> int:
    user_input = input("LearnAgent> ").strip()
    if not user_input:
        print("请输入学习主题、文档链接或 GitHub 仓库地址。")
        return 1
    print(asyncio.run(run_once(user_input)))
    return 0
