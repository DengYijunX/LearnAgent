"""DeepSeek OpenAI-compatible LLM client."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable
from urllib import error, request as urllib_request

from app.config.settings import Settings
from app.llm.base import LLMRequest, LLMResponse
from app.llm.model_selector import ModelSelector


Transport = Callable[
    [str, dict[str, str], dict[str, Any], int],
    Awaitable[dict[str, Any]],
]


class DeepSeekLLMClient:
    def __init__(
        self,
        settings: Settings,
        model_selector: ModelSelector,
        transport: Transport | None = None,
        timeout: int = 60,
    ):
        if not settings.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required for DeepSeekLLMClient")
        if not settings.deepseek_base_url:
            raise ValueError("DEEPSEEK_BASE_URL is required for DeepSeekLLMClient")

        self._settings = settings
        self._model_selector = model_selector
        self._transport = transport or _default_transport
        self._timeout = timeout

    async def chat(self, llm_request: LLMRequest) -> LLMResponse:
        payload = self._build_payload(llm_request)
        url = f"{self._settings.deepseek_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }

        raw = await self._transport(url, headers, payload, self._timeout)
        message = _extract_message(raw)
        return LLMResponse(
            content=message.get("content") or "",
            raw=raw,
            raw_json=json.dumps(raw, ensure_ascii=False),
            tool_calls=message.get("tool_calls") or [],
            usage=raw.get("usage") or {},
        )

    def _build_payload(self, llm_request: LLMRequest) -> dict[str, Any]:
        model = llm_request.model
        if not model:
            model = self._model_selector.select_for_mode(llm_request.mode).model
        if not model:
            raise ValueError("Selected model is empty. Configure DEEPSEEK_SMALL_MODEL or DEEPSEEK_LARGE_MODEL.")

        messages = list(llm_request.messages)
        if llm_request.system:
            messages = [{"role": "system", "content": llm_request.system}, *messages]

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": (
                llm_request.temperature
                if llm_request.temperature is not None
                else self._settings.llm_temperature
            ),
            "max_tokens": (
                llm_request.max_tokens
                if llm_request.max_tokens is not None
                else self._settings.llm_max_tokens
            ),
        }
        if llm_request.tools:
            payload["tools"] = [_to_openai_tool_schema(tool) for tool in llm_request.tools]
        return payload


def _extract_message(raw: dict[str, Any]) -> dict[str, Any]:
    choices = raw.get("choices") or []
    if not choices:
        return {}
    message = choices[0].get("message") or {}
    if isinstance(message, dict):
        return message
    return {}


def _to_openai_tool_schema(tool: dict[str, Any]) -> dict[str, Any]:
    if tool.get("type") == "function":
        return tool
    function: dict[str, Any] = {"name": tool["name"]}
    if "description" in tool:
        function["description"] = tool["description"]
    if "input_schema" in tool:
        function["parameters"] = tool["input_schema"]
    elif "parameters" in tool:
        function["parameters"] = tool["parameters"]
    return {"type": "function", "function": function}


async def _default_transport(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    return await asyncio.to_thread(_post_json, url, headers, payload, timeout)


def _post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(url=url, data=body, headers=headers, method="POST")
    try:
        with urllib_request.urlopen(req, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API request failed: HTTP {exc.code}: {detail}") from exc
    return json.loads(response_body)
