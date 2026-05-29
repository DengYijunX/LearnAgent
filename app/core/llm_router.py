"""LLM 驱动的意图路由器 —— 比正则规则更好地理解自然语言。"""

import json

from app.llm.base import LLMClient

CLASSIFY_PROMPT = """分析用户输入，返回JSON（只返回JSON，不要其他文字）：
{"intent":"learn_concept|analyze_repo|read_url|review|chat","topic":"提取的学习主题或null"}

规则：
- learn_concept：学习技术/概念/工具 → topic用简短英文标识
- analyze_repo：提到GitHub仓库链接 → topic=owner/repo
- read_url：提到网页链接需要读取 → topic=url
- review：复盘/回顾/总结学习内容 → topic=主题
- chat：闲聊/无学习意图/追问/继续 → topic=null"""


class LLMRouter:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    async def route(self, user_input: str) -> dict:
        """用 LLM 分类用户意图，返回 {intent, topic}。失败时降级为 chat。"""
        try:
            messages = [
                {"role": "system", "content": CLASSIFY_PROMPT},
                {"role": "user", "content": user_input},
            ]
            result = await self._llm.chat(messages=messages, max_tokens=80)
            content = result.get("content", "").strip()
            parsed = self._parse_json(content)
            if not parsed:
                return {"intent": "chat", "topic": None}
            intent = parsed.get("intent", "chat")
            if intent not in ("learn_concept", "analyze_repo", "read_url", "review", "chat"):
                intent = "chat"
            topic = parsed.get("topic")
            if topic and not isinstance(topic, str):
                topic = str(topic)
            return {"intent": intent, "topic": topic}
        except Exception:
            return {"intent": "chat", "topic": None}

    @staticmethod
    def _parse_json(text: str) -> dict | None:
        text = text.strip()
        # 去掉可能的 markdown 代码块包裹
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试提取第一个 { } 块
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
        return None
