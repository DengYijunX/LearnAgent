import pytest

from app.core.router import InputRouter


@pytest.mark.parametrize(
    ("text", "intent", "topic", "tools"),
    [
        (
            "我想学习 LangGraph",
            "learn_concept",
            "LangGraph",
            ["search_web"],
        ),
        (
            "https://docs.python.org/3/tutorial/index.html",
            "summarize_url",
            "https://docs.python.org/3/tutorial/index.html",
            ["read_url"],
        ),
        (
            "https://github.com/huggingface/smolagents 这个项目怎么学？",
            "analyze_repo",
            "https://github.com/huggingface/smolagents",
            ["github_repo_analyzer"],
        ),
        (
            "复盘一下我最近学的 agent 架构",
            "review_progress",
            "agent 架构",
            ["search_memory"],
        ),
        (
            "这个概念和 LangChain 有什么区别？",
            "simple_chat",
            "这个概念和 LangChain 有什么区别？",
            [],
        ),
    ],
)
def test_router_classifies_common_stage_one_inputs(text, intent, topic, tools):
    result = InputRouter().route(text)

    assert result.intent == intent
    assert result.topic == topic
    assert result.suggested_tools == tools
    assert 0 <= result.confidence <= 1


def test_router_rejects_blank_input():
    with pytest.raises(ValueError, match="empty"):
        InputRouter().route("   ")
