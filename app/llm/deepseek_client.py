import json
import logging
from app.llm.base import LLMClient

logger = logging.getLogger(__name__)


def _sanitize_str(s: str) -> str:
    """Remove lone surrogate characters that break JSON encoding on Windows."""
    return s.encode("utf-8", errors="surrogateescape").decode("utf-8", errors="replace")


def _sanitize(obj):
    """Recursively sanitize all strings in a dict/list structure."""
    if isinstance(obj, str):
        return _sanitize_str(obj)
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(item) for item in obj]
    return obj


def _validate_message_seq(messages: list[dict]) -> list[str]:
    """Validate tool message sequence — every tool result must have a
    matching tool_call in some preceding assistant message."""
    issues = []
    for i, m in enumerate(messages):
        if m.get("role") == "tool":
            tcid = m.get("tool_call_id", "")
            if not tcid:
                issues.append(f"msg[{i}]: tool message has empty tool_call_id")
            else:
                found = False
                for j in range(max(0, i - 20), i):
                    for tc in messages[j].get("tool_calls", []):
                        if tc.get("id") == tcid:
                            found = True
                            break
                    if found:
                        break
                if not found:
                    issues.append(
                        f"msg[{i}]: orphan tool (id={tcid[:24]}), "
                        f"no matching tool_calls in preceding 20 msgs"
                    )
    return issues


class DeepSeekLLMClient(LLMClient):
    """LLMClient backed by DeepSeek OpenAI-compatible API.

    Requires DEEPSEEK_API_KEY and DEEPSEEK_BASE_URL to be set via config.
    Uses httpx for async HTTP requests.
    """

    def __init__(self, api_key: str, base_url: str, model: str, temperature: float = 0.2, max_tokens: int = 2048):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def chat(
        self,
        messages: list[dict],
        system: str | None = None,
        tools: list[dict] | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        import httpx

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload: dict = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": max_tokens or self._max_tokens,
        }

        if system:
            payload["messages"] = [{"role": "system", "content": system}] + payload["messages"]

        if tools:
            payload["tools"] = [
                {"type": "function", "function": t} for t in tools
            ]

        payload = _sanitize(payload)

        # 检测孤立的 tool 消息（由 compaction 等 bug 导致）
        issues = _validate_message_seq(payload["messages"])
        if issues:
            for iss in issues:
                logger.warning("DeepSeek message seq: %s", iss)

        last_error = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(
                        f"{self._base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    if response.status_code >= 400:
                        try:
                            err_body = response.json()
                        except Exception:
                            err_body = response.text
                        raise RuntimeError(f"DeepSeek API error {response.status_code}: {err_body}")
                    data = response.json()
                    return data["choices"][0]["message"]
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < 2:
                    wait = (attempt + 1) * 2
                    logger.warning(f"API 请求失败（{type(e).__name__}），{wait}s 后重试 (attempt {attempt + 1}/3)")
                    import asyncio
                    await asyncio.sleep(wait)
                    continue
                raise RuntimeError(f"API 请求多次失败：{last_error}")

    async def stream_chat(
        self,
        messages: list[dict],
        system: str | None = None,
        tools: list[dict] | None = None,
    ):
        import httpx

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload: dict = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "stream": True,
        }

        if system:
            payload["messages"] = [{"role": "system", "content": system}] + payload["messages"]

        if tools:
            payload["tools"] = [
                {"type": "function", "function": t} for t in tools
            ]

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        chunk = line[6:]
                        if chunk == "[DONE]":
                            break
                        try:
                            yield json.loads(chunk)
                        except json.JSONDecodeError:
                            continue
