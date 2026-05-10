from abc import ABC, abstractmethod
from pydantic import BaseModel


class ToolSpec(BaseModel):
    name: str
    description: str = ""
    provider: str = ""
    required_config: list[str] = []
    risk_level: str = "low"


class ToolResult(BaseModel):
    ok: bool
    tool_name: str
    data: dict | list | str | None = None
    error: str | None = None
    metadata: dict = {}

    @classmethod
    def success(cls, tool_name: str, data=None, metadata: dict | None = None) -> "ToolResult":
        return cls(ok=True, tool_name=tool_name, data=data, metadata=metadata or {})

    @classmethod
    def failure(cls, tool_name: str, error: str, metadata: dict | None = None) -> "ToolResult":
        return cls(ok=False, tool_name=tool_name, error=error, metadata=metadata or {})


class BaseTool(ABC):
    spec: ToolSpec

    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        ...
