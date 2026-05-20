"""上下文构造器 —— 组装 Static Context + Dynamic Context。"""


STATIC_CONTEXT = """你是 LearnAgent，一个面向自学者的 AI 学习助手。
你的目标是帮助用户完成：发现 → 理解 → 实践 → 复盘 的学习闭环。

原则：
1. 先解释核心概念，再给例子。
2. 遇到新技术，应优先搜索可靠资料。
3. 不要假装读过资料。
4. 学习内容要分层递进。
5. 需要时生成练习任务。
6. 回复使用中文。"""


def build_system_prompt(
    current_topic: str | None = None,
    intent: str | None = None,
    user_level: str | None = None,
) -> str:
    parts = [STATIC_CONTEXT]

    dynamic = []
    if current_topic:
        dynamic.append(f"当前学习主题：{current_topic}")
    if intent:
        dynamic.append(f"当前意图：{intent}")
    if user_level:
        dynamic.append(f"用户水平：{user_level}")

    if dynamic:
        parts.append("\n<DYNAMIC_CONTEXT>\n" + "\n".join(dynamic) + "\n</DYNAMIC_CONTEXT>")

    return "\n\n".join(parts)
