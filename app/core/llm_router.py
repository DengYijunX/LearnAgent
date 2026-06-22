"""LLM 驱动的意图路由器 —— 比正则规则更好地理解自然语言。"""

import json

from app.llm.base import LLMClient

CLASSIFY_PROMPT = """你是学习意图分类器。分析用户输入，返回JSON（只返回JSON）：
{"intent":"learn_concept|analyze_repo|read_url|review|chat","topic":"英文主题词或null"}

规则（按优先级）：
- learn_concept：想学技术/做项目/写代码/实践。
  例："学python"→topic="python"
  例："我想用python生成个人主页"→topic="python-web"
  例："零基础 web开发"→topic="web-dev"
  例："帮我写一个Flask网站"→topic="flask"
  例："那个装饰器怎么用"→topic="python-decorators"
- analyze_repo：GitHub链接 → topic=owner/repo
- read_url：网页链接 → topic=url
- review：复盘/回顾/总结 → topic=主题
- chat：纯闲聊/打招呼/无技术意图 → topic=null
  注意：只要是涉及技术学习、代码、项目的，都不能判为chat！"""


# 兜底关键词：LLM 误判为 chat 但明显是学习意图时，强制纠正
# 注意避免太短的词（如"怎么"会误匹配"天气怎么样"）
_LEARN_KEYWORDS = [
    "学习", "教我", "怎么做", "如何做", "帮我写", "帮我做",
    "做一个", "写一个", "开发", "搭建", "入门", "教程",
    "生成", "创建", "练习", "实现", "写代码",
    "零基础", "新手", "从零",
]


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
            # 兜底：LLM 判为 chat 但明显是学习意图 → 纠正
            if intent == "chat" and any(kw in user_input for kw in _LEARN_KEYWORDS):
                intent = "learn_concept"
            topic = parsed.get("topic")
            if topic and not isinstance(topic, str):
                topic = str(topic)
            return {"intent": intent, "topic": topic}
        except Exception:
            # 异常降级时也用关键词兜底
            fallback = "learn_concept" if any(kw in user_input for kw in _LEARN_KEYWORDS) else "chat"
            return {"intent": fallback, "topic": None}

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
