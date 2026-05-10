from typing import Optional
from src.tools.base import BaseTool, ToolResult
from src.registry.permission import is_allowed
from src.logging_config import setup_logging

logger = setup_logging()


class ToolManager:
    """统一注册、权限检查、异常捕获、日志。"""
    def __init__(self, session_logger=None):
        self._tools: dict[str, BaseTool] = {}
        self._session_logger = session_logger

    def register(self, tool: BaseTool):
        self._tools[tool.spec.name] = tool
        logger.debug("tool registered", name=tool.spec.name)

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": t.spec.name,
                "description": t.spec.description,
                "provider": t.spec.provider,
                "risk_level": t.spec.risk_level,
            }
            for t in self._tools.values()
        ]

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    async def call(self, name: str, **kwargs) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult.failure(name, f"工具未注册: {name}")

        if not is_allowed(name):
            return ToolResult.failure(name, f"工具已禁用: {name}")

        try:
            result = await tool.run(**kwargs)
            if self._session_logger:
                self._session_logger.log("tool_call", {
                    "tool": name,
                    "ok": result.ok,
                    "error": result.error,
                    **result.metadata,
                })
            return result
        except Exception as e:
            logger.error("tool call failed", name=name, error=str(e))
            return ToolResult.failure(name, str(e))
