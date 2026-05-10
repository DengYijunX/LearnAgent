import json

import pytest


@pytest.mark.asyncio
async def test_tool_manager_returns_tool_result_and_blocks_disabled():
    from src.tools.base import BaseTool, ToolResult, ToolSpec
    from src.tools.manager import ToolManager

    class EchoTool(BaseTool):
        spec = ToolSpec(name="echo", description="Echo", provider="mock", risk_level="low")

        async def run(self, **kwargs):
            return ToolResult(ok=True, tool_name="echo", data=kwargs["text"])

    manager = ToolManager(permission=lambda name: name != "blocked")
    manager.register(EchoTool())

    result = await manager.call("echo", text="hi")
    missing = await manager.call("missing")

    assert result.ok is True
    assert result.data == "hi"
    assert missing.ok is False
    assert missing.error == "tool not registered"


def test_registry_status_and_prompt_loader(tmp_path):
    from src.core.prompt_registry import load_prompt
    from src.registry.registry import Registry

    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "router.md").write_text("route prompt", encoding="utf-8")

    registry = Registry()
    registry.register("memory", enabled=True, provider="file")

    assert registry.status()["memory"]["enabled"] is True
    assert load_prompt("router", prompt_dir) == "route prompt"


def test_artifact_writer_uses_dated_unique_names_and_index(tmp_path):
    from src.tools.artifact_writer import ArtifactWriter

    writer = ArtifactWriter(tmp_path)
    first = writer.write("summaries", "RAG", "# RAG")
    second = writer.write("summaries", "RAG", "# RAG again")

    assert first.path != second.path
    assert first.path.startswith("artifacts/summaries/")
    lines = (tmp_path / "data" / "artifacts_index.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["path"] for line in lines] == [first.path, second.path]


def test_config_validator_warns_by_default_and_raises_strict(monkeypatch):
    from src.registry.validator import validate_config

    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    warnings = validate_config(strict=False)
    assert any("OPENAI_API_KEY" in warning for warning in warnings)

    with pytest.raises(RuntimeError):
        validate_config(strict=True)
