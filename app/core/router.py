"""输入路由器 —— 基于规则匹配识别用户意图。"""

import re

GITHUB_URL_PATTERN = re.compile(r"https?://github\.com/[\w\-\.]+/[\w\-\.]+")
HTTP_URL_PATTERN = re.compile(r"https?://[^\s]+")
LEARN_KEYWORDS = ["学习", "了解", "学一下", "什么是", "讲讲", "教我", "解释", "介绍一下"]
REVIEW_KEYWORDS = ["复盘", "回顾", "总结", "复习"]


class InputRouter:
    def route(self, user_input: str) -> dict:
        text = user_input.strip()

        if GITHUB_URL_PATTERN.search(text):
            topic = self._extract_repo_topic(text)
            return {"intent": "analyze_repo", "topic": topic}

        if HTTP_URL_PATTERN.search(text):
            return {"intent": "read_url", "topic": text}

        for kw in REVIEW_KEYWORDS:
            if kw in text:
                return {"intent": "review", "topic": self._extract_topic(text)}

        for kw in LEARN_KEYWORDS:
            if kw in text:
                return {"intent": "learn_concept", "topic": self._extract_topic(text)}

        if not text:
            return {"intent": "chat", "topic": None}

        return {"intent": "chat", "topic": text if len(text) < 50 else text[:50]}

    def _extract_topic(self, text: str) -> str | None:
        for kw in LEARN_KEYWORDS + REVIEW_KEYWORDS:
            idx = text.find(kw)
            if idx >= 0:
                after = text[idx + len(kw):].strip()
                if after:
                    return after[:80]
                break
        return text[:80] if text else None

    def _extract_repo_topic(self, text: str) -> str | None:
        match = GITHUB_URL_PATTERN.search(text)
        if match:
            url = match.group()
            parts = url.rstrip("/").split("/")
            if len(parts) >= 2:
                return f"{parts[-2]}/{parts[-1]}"
            return url
        return None
