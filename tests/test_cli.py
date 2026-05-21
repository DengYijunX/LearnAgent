import pytest
import json
from types import SimpleNamespace

from app.entrypoint import cli
from app.entrypoint.cli import build_default_tool_registry, main, parse_args, run_once
from app.llm.mock_client import MockLLMClient
from app.tools.github_repo_analyzer import GitHubRepoAnalyzerTool


def test_build_default_tool_registry_registers_stage_one_tools():
    registry = build_default_tool_registry()

    assert registry.find("search_web") is not None
    assert registry.find("read_url") is not None
    assert registry.find("github_repo_analyzer") is not None
    assert isinstance(registry.find("github_repo_analyzer"), GitHubRepoAnalyzerTool)
    assert registry.find("learning_todo_write") is not None
    assert registry.find("search_memory") is not None
    assert registry.find("save_memory") is not None


@pytest.mark.asyncio
async def test_run_once_returns_mock_llm_response(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    output = await run_once("我想学习 LangGraph")

    assert "Mock response" in output


def test_parse_args_accepts_prompt_mode_and_real_flag():
    args = parse_args(["--real", "--json", "--mode", "deep", "我想学习 LangGraph"])

    assert args.real is True
    assert args.json is True
    assert args.mode == "deep"
    assert args.prompt == ["我想学习 LangGraph"]


def test_main_uses_prompt_argument_without_interactive_input(monkeypatch, capsys):
    async def fake_run_workflow_once(user_input, llm=None, mode=None):
        assert user_input == "我想学习 LangGraph"
        assert isinstance(llm, MockLLMClient)
        assert mode == "normal"
        return _fake_workflow_result(content="mock output")

    monkeypatch.setattr(cli, "run_workflow_once", fake_run_workflow_once)

    assert main(["我想学习 LangGraph"]) == 0
    assert "mock output" in capsys.readouterr().out


def test_main_can_print_json_output(monkeypatch, capsys):
    async def fake_run_workflow_once(user_input, llm=None, mode=None):
        return _fake_workflow_result(content="mock output")

    monkeypatch.setattr(cli, "run_workflow_once", fake_run_workflow_once)

    assert main(["--json", "我想学习 LangGraph"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["content"] == "mock output"
    assert payload["output"]["summary"] == "mock summary"
    assert payload["metadata"] == {"reason": "completed", "turns": 1}


def test_main_builds_real_llm_client_when_requested(monkeypatch, capsys):
    created = {}

    class FakeDeepSeekLLMClient:
        def __init__(self, settings, model_selector):
            created["settings"] = settings
            created["selector"] = model_selector

    async def fake_run_workflow_once(user_input, llm=None, mode=None):
        created["llm"] = llm
        created["mode"] = mode
        return _fake_workflow_result(content="real output")

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.example.test/v1")
    monkeypatch.setenv("DEEPSEEK_SMALL_MODEL", "small")
    monkeypatch.setenv("DEEPSEEK_LARGE_MODEL", "large")
    monkeypatch.setattr(cli, "DeepSeekLLMClient", FakeDeepSeekLLMClient)
    monkeypatch.setattr(cli, "run_workflow_once", fake_run_workflow_once)

    assert main(["--real", "--mode", "deep", "我想学习 LangGraph"]) == 0
    assert isinstance(created["llm"], FakeDeepSeekLLMClient)
    assert created["mode"] == "deep"
    assert "real output" in capsys.readouterr().out


def _fake_workflow_result(content: str):
    output = SimpleNamespace(to_dict=lambda: {"summary": "mock summary"})
    return SimpleNamespace(
        intent="learn_concept",
        topic="LangGraph",
        content=content,
        output=output,
        session_id="session-1",
        metadata={"reason": "completed", "turns": 1},
    )
