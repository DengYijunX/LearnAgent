"""输入路由器 —— 基于规则匹配识别用户意图，含 topic 归一化。"""

import re

GITHUB_URL_PATTERN = re.compile(r"https?://github\.com/[\w\-\.]+/[\w\-\.]+")
HTTP_URL_PATTERN = re.compile(r"https?://[^\s]+")
LEARN_KEYWORDS = ["学习", "了解", "学一下", "什么是", "讲讲", "教我", "解释", "介绍一下",
                  "怎么理解", "如何理解", "想学", "继续学习", "继续"]
REVIEW_KEYWORDS = ["复盘", "回顾", "总结", "复习"]

# topic 归一化时要清理的前后缀噪声词
NOISE_PREFIXES = ["学习", "继续学习", "继续", "了解", "讲讲", "介绍一下", "怎么理解", "如何理解", "教我", "什么是", "想学"]
NOISE_SUFFIXES = ["学习", "入门", "教程", "怎么用", "怎么学", "是什么", "的理解", "的用法", "的概念"]


def normalize_topic(raw: str | None) -> str | None:
    """规范化 topic：小写、去前后缀噪声、空格→连字符。"""
    if not raw:
        return None
    t = raw.strip().lower()
    for prefix in sorted(NOISE_PREFIXES, key=len, reverse=True):
        if t.startswith(prefix):
            t = t[len(prefix):]
            break
    for suffix in sorted(NOISE_SUFFIXES, key=len, reverse=True):
        if t.endswith(suffix):
            t = t[:-len(suffix)]
            break
    # 清理残留的前后空格和标点
    t = t.strip().strip("，。！？,.!?;；:：")
    if not t:
        return None
    # 空格/斜杠换连字符
    t = re.sub(r"\s+", "-", t)
    t = t.replace("/", "-")
    return t


def topic_distance(current: str | None, new: str | None) -> str:
    """判断新旧 topic 的关系：same / drift / switch。"""
    if new is None:
        return "same"
    if current is None:
        return "switch"
    if current == new:
        return "same"
    # containment：一个包含另一个
    if new in current or current in new:
        return "drift"
    # 共享单词
    cur_words = set(current.split("-"))
    new_words = set(new.split("-"))
    if cur_words & new_words:
        return "drift"
    return "switch"


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

        return {"intent": "chat", "topic": None}

    def _extract_topic(self, text: str) -> str | None:
        for kw in sorted(LEARN_KEYWORDS + REVIEW_KEYWORDS, key=len, reverse=True):
            idx = text.find(kw)
            if idx >= 0:
                after = text[idx + len(kw):].strip()
                if after:
                    return normalize_topic(after[:80])
                break
        raw = text[:80] if text else None
        return normalize_topic(raw)

    def _extract_repo_topic(self, text: str) -> str | None:
        match = GITHUB_URL_PATTERN.search(text)
        if match:
            url = match.group()
            parts = url.rstrip("/").split("/")
            if len(parts) >= 2:
                return f"{parts[-2]}/{parts[-1]}"
            return url
        return None
