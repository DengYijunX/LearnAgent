from abc import ABC, abstractmethod


class Tool(ABC):
    name: str
    description: str
    input_schema: dict

    def is_read_only(self) -> bool:
        return True

    def is_enabled(self) -> bool:
        return True

    @abstractmethod
    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        ...
