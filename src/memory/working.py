from typing import TypedDict, Annotated
from operator import add


class AgentState(TypedDict):
    """Agent 工作记忆。LangGraph 在节点间传递这个 state。"""
    user_query: str
    messages: Annotated[list[dict], add]
    intermediate_steps: Annotated[list[dict], add]
    final_answer: str
    error: str


def create_initial_state(user_query: str) -> AgentState:
    return AgentState(
        user_query=user_query,
        messages=[],
        intermediate_steps=[],
        final_answer="",
        error="",
    )
