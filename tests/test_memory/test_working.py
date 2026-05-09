from src.memory.working import create_initial_state


def test_create_initial_state():
    state = create_initial_state(user_query="什么是 RAG")
    assert state["user_query"] == "什么是 RAG"
    assert state["messages"] == []
    assert state["intermediate_steps"] == []
    assert state["final_answer"] == ""


def test_agent_state_append_message():
    state = create_initial_state(user_query="测试")
    state["messages"].append({"role": "assistant", "content": "你好"})
    assert len(state["messages"]) == 1


def test_agent_state_record_step():
    state = create_initial_state(user_query="测试")
    state["intermediate_steps"].append({"tool": "search", "result": "found 3 items"})
    assert len(state["intermediate_steps"]) == 1
