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
    permission_mode: str = "default",
) -> dict:
    search_count = 0
    useful_hits = 0
    MAX_SEARCHES = 3

    for _turn in range(max_turns):
        # 搜索次数超限时，注入强制回应指令
        if search_count >= MAX_SEARCHES:
            if useful_hits:
                msg = "你已经使用了全部搜索次数。请基于已有的信息回答用户。"
            else:
                msg = "你已经使用了全部搜索次数，但所有搜索都没有获取到有效信息。请直接告诉用户无法找到相关信息，建议用户自行搜索或访问官网。不要编造信息。"
            inject = {"role": "system", "content": msg}
            messages.append(inject)
            assistant_message = await llm.chat(
                messages=messages,
                system=system,
                tools=[],  # 不再提供工具，强制 LLM 文字回复
            )
            messages.append(assistant_message)
            return {"messages": messages, "reason": "max_searches"}

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
                "max_turns": max_turns,
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

            # 统计搜索和读取次数
            if call["name"] in ("search_web", "read_url"):
                search_count += 1

            # 权限判定：只读自动通过，plan mode 禁止写入
            if tool.is_read_only():
                pass
            else:
                decision = check_permission(tool, call["input"], mode=permission_mode)
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

                # 检查搜索/读取结果是否包含有效数据
                if call["name"] == "search_web" and result.get("results"):
                    useful_hits += 1
                elif call["name"] == "read_url" and len(result.get("content", "")) > 50:
                    useful_hits += 1

                summary, extra = _summarize_result(call["name"], result)
                if on_event:
                    await on_event("tool_end", {
                        "name": call["name"],
                        "elapsed": elapsed,
                        "is_error": result.get("isError", False),
                        "result_summary": summary,
                        **extra,
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


def _summarize_result(tool_name: str, result: dict) -> tuple[str, dict]:
    """Generate a one-line summary and extra data (like search titles)."""
    extra = {}
    if result.get("isError"):
        err = (result.get("error") or result.get("stderr") or "未知错误")
        # 去掉换行，截断
        err = str(err).replace("\n", " ")[:250]
        return err, extra
    if tool_name == "search_web":
        n = len(result.get("results", []))
        extra["result_titles"] = [r.get("title", "") for r in result.get("results", [])]
        return f"找到 {n} 条搜索结果", extra
    if tool_name == "read_url":
        content = result.get("content", "")
        return f"读取网页，{len(content)} 字符", extra
    if tool_name == "analyze_github_repo":
        content = result.get("content", "")
        return f"分析仓库，{len(content)} 字符", extra
    if tool_name == "file_write":
        return f"写入文件 {result.get('path', '?')}", extra
    if tool_name == "file_read":
        content = result.get("content", "")
        return f"读取文件，{len(content)} 字符", extra
    if tool_name == "run_code":
        stdout = result.get("stdout", "")
        returncode = result.get("returncode", "?")
        return f"执行完毕 (exit={returncode})，输出 {len(stdout)} 字符", extra
    if tool_name == "list_files":
        files = result.get("files", "")
        return f"列出文件" + (f"：{files[:60]}" if files else "（空）"), extra
    if tool_name == "learning_todo_write":
        return f"保存 {result.get('count', 0)} 项学习任务", extra
    return "完成", extra
