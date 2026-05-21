"""Minimal LearnAgent loop with tool-call support."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from app.llm.base import LLMClient, LLMRequest, LLMResponse
from app.tools.base import ToolResult
from app.tools.registry import ToolRegistry


@dataclass(frozen=True)
class AgentLoopResult:
    messages: list[dict[str, Any]]
    final_content: str
    reason: str
    turns: int


@dataclass(frozen=True)
class ParsedToolCall:
    id: str
    name: str
    arguments: dict[str, Any]
    is_native: bool = False


async def run_agent_loop(
    llm: LLMClient,
    tools: ToolRegistry,
    messages: list[dict[str, Any]],
    system_prompt: str | None = None,
    mode: str | None = None,
    max_turns: int = 4,
) -> AgentLoopResult:
    current_messages = list(messages)
    final_content = ""
    allow_tools = True

    for turn in range(1, max_turns + 1):
        response = await llm.chat(
            LLMRequest(
                messages=[dict(message) for message in current_messages],
                system=system_prompt,
                tools=tools.to_api_schema() if allow_tools else [],
                mode=mode,
            )
        )
        final_content = response.content
        assistant_message: dict[str, Any] = {"role": "assistant", "content": response.content}
        if response.tool_calls:
            assistant_message["tool_calls"] = response.tool_calls
        current_messages.append(assistant_message)

        tool_calls = _parse_tool_calls(response)
        if not tool_calls:
            return AgentLoopResult(
                messages=current_messages,
                final_content=final_content,
                reason="completed",
                turns=turn,
            )

        for call in tool_calls:
            tool_result = await _execute_tool_call(call, tools)
            current_messages.append(
                _tool_result_message(call, tool_result)
            )
        allow_tools = False

    return AgentLoopResult(
        messages=current_messages,
        final_content=final_content,
        reason="max_turns",
        turns=max_turns,
    )


async def _execute_tool_call(call: ParsedToolCall, tools: ToolRegistry) -> ToolResult:
    tool = tools.find(call.name)
    if tool is None:
        return ToolResult(content=f"Unknown tool: {call.name}", is_error=True)
    try:
        return await tool.call(call.arguments, context={})
    except Exception as exc:
        return ToolResult(content=f"Tool {call.name} failed: {exc}", is_error=True)


def _parse_tool_calls(response: LLMResponse) -> list[ParsedToolCall]:
    if response.tool_calls:
        return [_parse_standard_tool_call(call) for call in response.tool_calls]
    json_action = _parse_json_action(response.content)
    if json_action is None:
        return []
    return [json_action]


def _parse_standard_tool_call(call: dict[str, Any]) -> ParsedToolCall:
    function = call.get("function") or {}
    raw_arguments = function.get("arguments") or "{}"
    arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
    return ParsedToolCall(
        id=str(call.get("id") or function.get("name") or "tool_call"),
        name=str(function.get("name") or call.get("name")),
        arguments=arguments,
        is_native=True,
    )


def _parse_json_action(content: str) -> ParsedToolCall | None:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or "action" not in payload:
        return None
    arguments = payload.get("arguments") or {}
    if not isinstance(arguments, dict):
        arguments = {}
    return ParsedToolCall(
        id=str(payload.get("id") or payload["action"]),
        name=str(payload["action"]),
        arguments=arguments,
        is_native=False,
    )


def _tool_result_message(call: ParsedToolCall, tool_result: ToolResult) -> dict[str, Any]:
    if call.is_native:
        return {
            "role": "tool",
            "tool_call_id": call.id,
            "name": call.name,
            "content": tool_result.content,
            "is_error": tool_result.is_error,
        }
    return {
        "role": "user",
        "content": tool_result.content,
        "name": call.name,
        "is_error": tool_result.is_error,
    }
