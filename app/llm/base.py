from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        system: str | None = None,
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
    ) -> dict:
        ...

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict],
        system: str | None = None,
        tools: list[dict] | None = None,
    ):
        ...
