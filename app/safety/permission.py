from dataclasses import dataclass

from app.tools.base import Tool


@dataclass
class PermissionDecision:
    behavior: str  # "allow" | "ask" | "deny"
    reason: str = ""


def check_permission(
    tool: Tool,
    tool_input: dict,
    mode: str = "default",
) -> PermissionDecision:
    if mode == "plan" and not tool.is_read_only():
        return PermissionDecision("deny", "Plan mode blocks write actions")

    if tool.is_read_only():
        return PermissionDecision("allow", "Read-only tool")

    return PermissionDecision("ask", "Tool writes local state")
