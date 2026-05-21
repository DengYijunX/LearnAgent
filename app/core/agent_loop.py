import json

from app.llm.base import LLMClient
from app.tools.registry import ToolRegistry
from app.safety.permission import check_permission, PermissionDecision


def extract_tool_calls(assistant_message: dict) -> list[dict]:
    """Extract tool_calls from an assistant message in OpenAI-compatible format."""
    tool_calls = assistant_message.get("tool_calls", [])
    if not tool_calls:
        return []
    result = []
    for tc in tool_calls:
        func = tc.get("function", {})
        name = func.get("name", "")
        try:
            arguments = json.loads(func.get("arguments", "{}"))
        except json.JSONDecodeError:
            arguments = {}
        result.append({"id": tc.get("id", ""), "name": name, "input": arguments})
    return result


def format_tool_result(tool_call_id: str, result: dict) -> dict:
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": json.dumps(result, ensure_ascii=False),
    }


def format_error_result(tool_call_id: str, error: str) -> dict:
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": error,
        "is_error": True,
    }


async def agent_loop(
    messages: list[dict],
    llm: LLMClient,
    tools: ToolRegistry,
    system: str | None = None,
    max_turns: int = 8,
    ask_callback=None,
) -> dict:
    for _turn in range(max_turns):
        assistant_message = await llm.chat(
            messages=messages,
            system=system,
            tools=tools.to_api_schema(),
        )

        messages.append(assistant_message)

        tool_calls = extract_tool_calls(assistant_message)
        if not tool_calls:
            return {"messages": messages, "reason": "completed"}

        tool_results = []

        for call in tool_calls:
            tool = tools.find(call["name"])
            if tool is None:
                tool_results.append(
                    format_error_result(call["id"], f"Unknown tool: {call['name']}")
                )
                continue

            decision = check_permission(tool, call["input"])
            if decision.behavior == "deny":
                tool_results.append(
                    format_error_result(call["id"], decision.reason)
                )
                continue

            if decision.behavior == "ask":
                if ask_callback:
                    approved = await ask_callback(tool.name, decision.reason)
                    if not approved:
                        tool_results.append(
                            format_error_result(call["id"], "用户拒绝了此操作")
                        )
                        continue

            try:
                result = await tool.call(call["input"])
                tool_results.append(format_tool_result(call["id"], result))
            except Exception as exc:
                tool_results.append(
                    format_error_result(call["id"], f"Tool error: {exc}")
                )

        for tr in tool_results:
            messages.append(tr)

    return {"messages": messages, "reason": "max_turns"}
