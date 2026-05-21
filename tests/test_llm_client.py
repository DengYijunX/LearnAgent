import json
import pytest

from app.config.settings import Settings
from app.llm.base import LLMRequest, LLMResponse
from app.llm.deepseek_client import DeepSeekLLMClient
from app.llm.mock_client import MockLLMClient
from app.llm.model_selector import ModelSelector


@pytest.mark.asyncio
async def test_mock_llm_client_returns_configured_response():
    client = MockLLMClient(
        response=LLMResponse(content="学习路线已生成", raw={"source": "test"})
    )

    response = await client.chat(
        LLMRequest(messages=[{"role": "user", "content": "我想学习 LangGraph"}])
    )

    assert response.content == "学习路线已生成"
    assert response.raw == {"source": "test"}


@pytest.mark.asyncio
async def test_mock_llm_client_uses_default_response():
    response = await MockLLMClient().chat(
        LLMRequest(messages=[{"role": "user", "content": "hello"}])
    )

    assert "mock" in response.content.lower()


def test_deepseek_client_rejects_missing_api_key():
    settings = Settings(
        deepseek_base_url="https://api.example.test/v1",
        deepseek_small_model="deepseek-flash-id",
    )

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        DeepSeekLLMClient(settings=settings, model_selector=ModelSelector(settings))


def test_deepseek_client_rejects_missing_base_url():
    settings = Settings(
        deepseek_api_key="test-key",
        deepseek_small_model="deepseek-flash-id",
    )

    with pytest.raises(ValueError, match="DEEPSEEK_BASE_URL"):
        DeepSeekLLMClient(settings=settings, model_selector=ModelSelector(settings))


@pytest.mark.asyncio
async def test_deepseek_client_builds_openai_compatible_request():
    captured = {}
    settings = Settings(
        deepseek_api_key="test-key",
        deepseek_base_url="https://api.example.test/v1",
        deepseek_small_model="deepseek-flash-id",
        deepseek_large_model="deepseek-pro-id",
        llm_temperature=0.3,
        llm_max_tokens=4096,
    )

    async def fake_transport(url, headers, payload, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["payload"] = payload
        captured["timeout"] = timeout
        return {
            "choices": [
                {
                    "message": {
                        "content": "真实模型响应",
                        "tool_calls": [{"id": "call_1"}],
                    }
                }
            ],
            "usage": {"total_tokens": 12},
        }

    client = DeepSeekLLMClient(
        settings=settings,
        model_selector=ModelSelector(settings),
        transport=fake_transport,
    )

    response = await client.chat(
        LLMRequest(
            messages=[{"role": "user", "content": "总结一下 LangGraph"}],
            system="你是 LearnAgent",
            tools=[{"name": "search_web"}],
            mode="deep",
        )
    )

    assert captured["url"] == "https://api.example.test/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["headers"]["Content-Type"] == "application/json"
    assert captured["payload"]["model"] == "deepseek-pro-id"
    assert captured["payload"]["temperature"] == 0.3
    assert captured["payload"]["max_tokens"] == 4096
    assert captured["payload"]["tools"] == [
        {
            "type": "function",
            "function": {
                "name": "search_web",
            },
        }
    ]
    assert captured["payload"]["messages"] == [
        {"role": "system", "content": "你是 LearnAgent"},
        {"role": "user", "content": "总结一下 LangGraph"},
    ]
    assert captured["timeout"] == 60
    assert response.content == "真实模型响应"
    assert response.tool_calls == [{"id": "call_1"}]
    assert response.usage == {"total_tokens": 12}
    assert json.loads(response.raw_json)["choices"][0]["message"]["content"] == "真实模型响应"
