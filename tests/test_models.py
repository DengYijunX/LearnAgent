from src.models.schemas import UserInput, TaskType, KnowledgeSummary


def test_user_input_parsing():
    ui = UserInput(query="什么是 RAG")
    assert ui.query == "什么是 RAG"
    assert ui.input_type == "keyword"  # 默认推断


def test_user_input_with_url():
    ui = UserInput(query="https://github.com/langchain-ai/langgraph")
    assert ui.input_type == "github_url"


def test_user_input_with_doc_url():
    ui = UserInput(query="https://docs.python.org/3/library/asyncio.html")
    assert ui.input_type == "doc_url"


def test_task_type_enum():
    assert TaskType.SIMPLE.value == "simple"
    assert TaskType.COMPLEX.value == "complex"


def test_knowledge_summary():
    ks = KnowledgeSummary(
        topic="RAG",
        core_concepts=["检索", "增强", "生成"],
        learning_points=["向量数据库的选择", "Embedding 的作用"],
        related_techs=["LangChain", "LlamaIndex", "向量数据库"],
    )
    assert len(ks.core_concepts) == 3
