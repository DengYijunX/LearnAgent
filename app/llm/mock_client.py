from app.llm.base import LLMClient


class MockLLMClient(LLMClient):
    """A deterministic mock LLM client for testing Agent Loop without real API.

    If respond_with_tool=True and tools are provided, returns a tool_use response.
    Otherwise returns a plain text response.
    """

    def __init__(self, respond_with_tool: bool = False):
        self._respond_with_tool = respond_with_tool

    async def chat(
        self,
        messages: list[dict],
        system: str | None = None,
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> dict:
        return self.chat_sync(messages, system, tools, max_tokens)

    def chat_sync(
        self,
        messages: list[dict],
        system: str | None = None,
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> dict:
        if self._respond_with_tool and tools:
            tool = tools[0]
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_mock_001",
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "arguments": '{"query": "mock query"}',
                        },
                    }
                ],
            }
        return {
            "role": "assistant",
            "content": "This is a mock response from MockLLMClient.",
        }

    async def stream_chat(
        self,
        messages: list[dict],
        system: str | None = None,
        tools: list[dict] | None = None,
    ):
        result = self.chat_sync(messages, system, tools)
        yield result
