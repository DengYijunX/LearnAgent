from abc import ABC, abstractmethod

from app.logging import log_tool


class Tool(ABC):
    name: str
    description: str
    input_schema: dict

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # 自动为所有 Tool 子类的 call 方法加上日志装饰器
        if "call" in cls.__dict__:
            cls.call = log_tool(cls.__dict__["call"])

    def is_read_only(self) -> bool:
        return True

    def is_enabled(self) -> bool:
        return True

    @abstractmethod
    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        ...
