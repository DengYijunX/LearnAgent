from app.llm.base import LLMClient


class MockLLMClient(LLMClient):
    """A deterministic mock LLM client for testing Agent Loop without real API.

    Parameters:
        respond_with_tool: If True, returns tool_use on early turns (up to tool_turns),
                           then switches to text on later turns.
        tool_turns: Number of turns to return tool_use before switching to text.
                    Only used when respond_with_tool=True.
    """

    def __init__(self, respond_with_tool: bool = False, tool_turns: int = 1):
        self._respond_with_tool = respond_with_tool
        self._tool_turns = tool_turns
        self._turn_count = 0

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
        self._turn_count += 1

        # Count previous assistant messages to know which turn we're on
        assistant_turns = sum(1 for m in messages if m.get("role") == "assistant")

        if self._respond_with_tool and tools and assistant_turns < self._tool_turns:
            tool = tools[0]
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": f"call_mock_{assistant_turns:03d}",
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
            "content": (
                "这是 MockLLMClient 的回复。"
                "我已根据你的输入和工具结果生成了学习内容摘要。"
                "在实际接入 DeepSeek 后，这里会是真实的学习路线和概念解释。"
            ),
        }

    async def stream_chat(
        self,
        messages: list[dict],
        system: str | None = None,
        tools: list[dict] | None = None,
    ):
        result = self.chat_sync(messages, system, tools)
        yield result
