from app.core.output_schema import LearningOutput


def test_learning_output_uses_plain_text_as_summary():
    output = LearningOutput.from_text("LangGraph 是用于构建有状态 Agent 工作流的框架。")

    assert output.summary == "LangGraph 是用于构建有状态 Agent 工作流的框架。"
    assert output.concepts == []
    assert output.learning_path == []
    assert output.practice_tasks == []
    assert output.related_topics == []
    assert output.sources == []


def test_learning_output_parses_json_fields():
    output = LearningOutput.from_text(
        """
        {
          "summary": "LangGraph 用于有状态 Agent 工作流。",
          "concepts": ["StateGraph", "Node", "Edge"],
          "learning_path": ["理解状态", "实现第一个图"],
          "practice_tasks": ["写一个两节点图"],
          "related_topics": ["LangChain"],
          "sources": ["https://example.com/langgraph"]
        }
        """
    )

    assert output.summary == "LangGraph 用于有状态 Agent 工作流。"
    assert output.concepts == ["StateGraph", "Node", "Edge"]
    assert output.learning_path == ["理解状态", "实现第一个图"]
    assert output.practice_tasks == ["写一个两节点图"]
    assert output.related_topics == ["LangChain"]
    assert output.sources == ["https://example.com/langgraph"]


def test_learning_output_to_dict_is_stable():
    output = LearningOutput(summary="s", concepts=["c"])

    assert output.to_dict() == {
        "summary": "s",
        "concepts": ["c"],
        "learning_path": [],
        "practice_tasks": [],
        "related_topics": [],
        "sources": [],
    }
