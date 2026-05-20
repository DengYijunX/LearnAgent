import pytest

from app.entrypoint.cli import build_default_tool_registry, run_once


def test_build_default_tool_registry_registers_stage_one_mock_tools():
    registry = build_default_tool_registry()

    assert registry.find("search_web") is not None
    assert registry.find("read_url") is not None
    assert registry.find("github_repo_analyzer") is not None
    assert registry.find("learning_todo_write") is not None


@pytest.mark.asyncio
async def test_run_once_returns_mock_llm_response(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    output = await run_once("我想学习 LangGraph")

    assert "Mock response" in output
