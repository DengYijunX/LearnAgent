import json
from app.llm.base import LLMClient


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

        async with httpx.AsyncClient(timeout=60) as client:
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
