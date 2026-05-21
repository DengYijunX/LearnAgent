import json
import time

from app.llm.base import LLMClient
from app.tools.registry import ToolRegistry
from app.safety.permission import check_permission, PermissionDecision


def extract_tool_calls(assistant_message: dict) -> list[dict]:
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
    on_event=None,
) -> dict:
    for _turn in range(max_turns):
        # 通知：开始思考
        if on_event:
            await on_event("thinking", {"turn": _turn + 1, "max_turns": max_turns})

        assistant_message = await llm.chat(
            messages=messages,
            system=system,
            tools=tools.to_api_schema(),
        )

        messages.append(assistant_message)
        content_len = len(assistant_message.get("content") or "")
        if on_event:
            await on_event("thought", {
                "turn": _turn + 1,
                "has_content": content_len > 0,
                "content_len": content_len,
            })

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
                    approved = await ask_callback(tool.name, decision.reason, call["input"])
                    if not approved:
                        tool_results.append(
                            format_error_result(call["id"], "用户拒绝了此操作")
                        )
                        continue

            # 通知：工具开始执行
            t0 = time.time()
            if on_event:
                await on_event("tool_start", {
                    "name": call["name"],
                    "input": call["input"],
                    "turn": _turn + 1,
                })

            try:
                result = await tool.call(call["input"])
                elapsed = time.time() - t0
                if on_event:
                    await on_event("tool_end", {
                        "name": call["name"],
                        "elapsed": elapsed,
                        "is_error": result.get("isError", False),
                        "result_summary": _summarize_result(call["name"], result),
                    })
                tool_results.append(format_tool_result(call["id"], result))
            except Exception as exc:
                elapsed = time.time() - t0
                if on_event:
                    await on_event("tool_end", {
                        "name": call["name"],
                        "elapsed": elapsed,
                        "is_error": True,
                        "result_summary": str(exc)[:100],
                    })
                tool_results.append(
                    format_error_result(call["id"], f"Tool error: {exc}")
                )

        for tr in tool_results:
            messages.append(tr)

    return {"messages": messages, "reason": "max_turns"}


def _summarize_result(tool_name: str, result: dict) -> str:
    """Generate a one-line summary of tool execution result."""
    if result.get("isError"):
        return result.get("error", "未知错误")[:80]
    if tool_name == "search_web":
        n = len(result.get("results", []))
        return f"找到 {n} 条搜索结果"
    if tool_name == "read_url":
        content = result.get("content", "")
        return f"读取网页，{len(content)} 字符"
    if tool_name == "analyze_github_repo":
        content = result.get("content", "")
        return f"分析仓库，{len(content)} 字符"
    if tool_name == "file_write":
        return f"写入文件 {result.get('path', '?')}"
    if tool_name == "file_read":
        content = result.get("content", "")
        return f"读取文件，{len(content)} 字符"
    if tool_name == "run_code":
        stdout = result.get("stdout", "")
        returncode = result.get("returncode", "?")
        return f"执行完毕 (exit={returncode})，输出 {len(stdout)} 字符"
    if tool_name == "list_files":
        files = result.get("files", "")
        return f"列出文件" + (f"：{files[:60]}" if files else "（空）")
    if tool_name == "learning_todo_write":
        return f"保存 {result.get('count', 0)} 项学习任务"
    return "完成"
