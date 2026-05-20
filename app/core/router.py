"""Rule-based input router for stage one."""

from __future__ import annotations

from dataclasses import dataclass, field
import re


URL_PATTERN = re.compile(r"https?://[^\s]+")
GITHUB_REPO_PATTERN = re.compile(r"https?://github\.com/[^/\s]+/[^/\s?#]+")


@dataclass(frozen=True)
class RouteResult:
    intent: str
    topic: str
    confidence: float
    suggested_tools: list[str] = field(default_factory=list)


class InputRouter:
    def route(self, user_input: str) -> RouteResult:
        text = user_input.strip()
        if not text:
            raise ValueError("Cannot route empty input")

        github_match = GITHUB_REPO_PATTERN.search(text)
        if github_match:
            return RouteResult(
                intent="analyze_repo",
                topic=github_match.group(0),
                confidence=0.95,
                suggested_tools=["github_repo_analyzer"],
            )

        url_match = URL_PATTERN.search(text)
        if url_match:
            return RouteResult(
                intent="summarize_url",
                topic=url_match.group(0),
                confidence=0.9,
                suggested_tools=["read_url"],
            )

        if _looks_like_review_request(text):
            return RouteResult(
                intent="review_progress",
                topic=_extract_review_topic(text),
                confidence=0.85,
                suggested_tools=["search_memory"],
            )

        if _looks_like_learning_request(text):
            return RouteResult(
                intent="learn_concept",
                topic=_extract_learning_topic(text),
                confidence=0.82,
                suggested_tools=["search_web"],
            )

        return RouteResult(
            intent="simple_chat",
            topic=text,
            confidence=0.5,
            suggested_tools=[],
        )


def _looks_like_learning_request(text: str) -> bool:
    return any(marker in text for marker in ("学习", "了解", "入门"))


def _looks_like_review_request(text: str) -> bool:
    return any(marker in text for marker in ("复盘", "回顾", "总结最近"))


def _extract_learning_topic(text: str) -> str:
    cleaned = text
    for marker in ("我想学习", "想学习", "学习", "了解", "入门"):
        cleaned = cleaned.replace(marker, " ")
    return cleaned.strip(" ：:？?。") or text


def _extract_review_topic(text: str) -> str:
    cleaned = text
    for marker in ("复盘一下", "复盘", "回顾一下", "回顾", "我最近学的", "最近学的"):
        cleaned = cleaned.replace(marker, " ")
    return cleaned.strip(" ：:？?。") or text
