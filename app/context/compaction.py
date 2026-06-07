"""上下文压缩 —— 长对话自动摘要旧消息，防止撑爆上下文窗口。

压缩时必须保持 tool_calls ↔ tool_result 链完整，否则 API 会拒绝。
"""

from app.llm.base import LLMClient

# 粗略估算：中英文混合约 2-4 字符/token，取低估值防止超限
CHARS_PER_TOKEN = 2.5

# 预算阈值
BUDGET_WARNING = 8000   # tokens
BUDGET_CRITICAL = 12000  # tokens
SAFE_TAIL = 6  # 保留最近 N 条消息不压缩


def _find_safe_split(messages: list[dict], max_tail: int) -> int:
    """找到安全的切分点，确保 tool 消息不会脱离其 tool_calls。

    规则：
    1. 初始切分点 split = len(messages) - max_tail
    2. 如果 recent 段内有 tool 消息，其 tool_calls 对应的 assistant 消息
       必须在同一段内 — 向前扩展 split 直到条件满足。

    返回安全的 split 位置（old 段结束，recent 段开始）。
    """
    split = max(0, len(messages) - max_tail)
    if split == 0:
        return 0

    # 收集 recent 段中所有 tool 消息的 tool_call_id
    while True:
        required_ids: set[str] = set()
        for m in messages[split:]:
            if m.get("role") == "tool":
                tcid = m.get("tool_call_id", "")
                if tcid:
                    required_ids.add(tcid)

        if not required_ids:
            break  # recent 段没有 tool 消息，安全

        # 检查这些 id 对应的 assistant 消息是否都在 recent 段
        missing = set(required_ids)
        for m in messages[split:]:
            if m.get("role") == "assistant":
                for tc in m.get("tool_calls", []):
                    tc_id = tc.get("id", "")
                    missing.discard(tc_id)

        if not missing:
            break  # 所有 tool 消息的 tool_calls 都在 recent 段内，安全

        # 需要向前扩展 split，找到包含缺失 tool_call 的 assistant 消息
        extended = split
        for i in range(split - 1, -1, -1):
            m = messages[i]
            if m.get("role") == "assistant":
                for tc in m.get("tool_calls", []):
                    tc_id = tc.get("id", "")
                    if tc_id in missing:
                        extended = min(extended, i)

        if extended == split:
            break  # 没找到，可能已经扩展到头了
        split = extended

    return split


def estimate_tokens(messages: list[dict]) -> int:
    """粗略估算消息列表的 token 数。"""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += len(content) / CHARS_PER_TOKEN
        # tool_calls 也估算
        for tc in msg.get("tool_calls", []):
            args = tc.get("function", {}).get("arguments", "")
            total += len(args) / CHARS_PER_TOKEN
    return int(total)


def compact_messages(messages: list[dict]) -> tuple[list[dict], int]:
    """
    压缩消息列表：保留尾部 SAFE_TAIL 条，之前的用摘要替代。
    保证不会拆开 tool_calls ↔ tool_result 链。
    返回 (compacted_messages, removed_count)。
    """
    tokens = estimate_tokens(messages)
    if tokens < BUDGET_WARNING:
        return messages, 0

    if len(messages) <= SAFE_TAIL + 4:
        return messages, 0

    split = _find_safe_split(messages, SAFE_TAIL)

    if split == 0:
        return messages, 0  # 无法安全压缩

    old = messages[:split]
    recent = messages[split:]

    if not old:
        return messages, 0

    # 生成摘要
    summary_parts = []
    for msg in old:
        role = msg.get("role", "?")
        content = msg.get("content", "")
        if content and isinstance(content, str) and len(content) > 20:
            short = content[:200].replace("\n", " ")
            summary_parts.append(f"[{role}] {short}")

    summary = "以下是之前对话的摘要：\n" + "\n".join(summary_parts[-20:])

    compacted = [{"role": "user", "content": summary}] + recent
    return compacted, len(old)


async def llm_compact(messages: list[dict], llm: LLMClient) -> list[dict]:
    """
    使用 LLM 生成更精炼的压缩摘要（需要 LLM 调用一次）。
    保证不会拆开 tool_calls ↔ tool_result 链。
    返回压缩后的消息列表。
    """
    tokens = estimate_tokens(messages)
    if tokens < BUDGET_CRITICAL:
        return messages

    if len(messages) <= SAFE_TAIL + 6:
        return messages

    split = _find_safe_split(messages, SAFE_TAIL)

    if split == 0:
        return messages

    old = messages[:split]
    recent = messages[split:]

    if not old:
        return messages

    compact_prompt = (
        "请用 200 字以内总结以下对话的关键内容，只保留学习相关的知识点和用户问题。"
        "不要丢失用户的学习意图和已讲解过的概念。"
    )
    old_text = "\n".join(
        f"[{m.get('role', '?')}]: {str(m.get('content', ''))[:300]}"
        for m in old[-30:]  # 最多取最近 30 条旧消息
    )

    try:
        result = await llm.chat(
            messages=[{"role": "user", "content": f"{compact_prompt}\n\n{old_text}"}],
            max_tokens=300,
        )
        summary = result.get("content", "") or "(摘要生成失败)"
    except Exception:
        summary = "(摘要生成失败)"

    return [{"role": "user", "content": f"[上下文压缩] {summary}"}] + recent
