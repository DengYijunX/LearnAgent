import json
import os
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import settings
from src.memory.working import AgentState
from src.tools.filesystem import create_project, write_file
from src.logging_config import setup_logging

logger = setup_logging()

PLAN_PROMPT = """你是技术教学专家。为用户要学的技术设计渐进式教学场景。

规则：
- 3-5 个步骤，从易到难
- 每一步包含：场景描述、要创建的文件及完整代码
- 代码可以是 Python/JS/YAML 等，确保可以直接运行

返回 JSON：
{
  "steps": [
    {
      "title": "场景名",
      "description": "本步骤学什么",
      "files": {"文件名": "文件完整内容"}
    }
  ]
}"""


async def plan_node(state: AgentState) -> dict:
    """制定教学计划"""
    logger.info("plan_node 开始", query=state["user_query"][:50])
    llm = ChatAnthropic(
        model=settings.anthropic_model_complex,
        api_key=settings.anthropic_api_key,
        max_tokens=4000,
    )
    msgs = [
        SystemMessage(content=PLAN_PROMPT),
        HumanMessage(content=f"用户要学：{state['user_query']}"),
    ]
    response = await llm.ainvoke(msgs)
    content = response.content.strip()
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    plan = json.loads(content)
    logger.info("plan_node 完成", step_count=len(plan["steps"]))
    return {
        "plan": plan,
        "messages": [{"role": "assistant", "content": f"制定了 {len(plan['steps'])} 步学习计划"}],
    }


async def execute_node(state: AgentState) -> dict:
    """执行当前教学步骤：创建文件"""
    plan = state.get("plan", {})
    steps = plan.get("steps", [])
    current_step = state.get("current_step", 0)

    if current_step >= len(steps):
        return {"messages": [{"role": "assistant", "content": "所有步骤已完成！"}]}

    step = steps[current_step]
    project_dir = state.get("project_dir", f"./projects/{state['user_query'].replace(' ', '-')}")

    logger.info("execute_node", step=current_step + 1, title=step["title"])

    # 首次执行时创建项目目录
    if current_step == 0:
        base = os.path.expanduser("~/LearnAgent/projects")
        create_project(base, state["user_query"].replace(" ", "-"))

    step_result = {"step": current_step + 1, "title": step["title"], "description": step["description"], "files": []}
    for filename, content in step.get("files", {}).items():
        file_path = write_file(project_dir, filename, content)
        step_result["files"].append(file_path)

    return {
        "current_step": current_step + 1,
        "messages": [{"role": "assistant", "content": json.dumps(step_result, ensure_ascii=False)}],
        "project_dir": project_dir,
    }


async def summarize_node(state: AgentState) -> dict:
    """教学完成后的总结"""
    return {
        "messages": [{"role": "assistant", "content": "教学项目已全部完成！你可以运行项目查看效果。"}],
    }


def should_continue(state: AgentState) -> str:
    """判断是否还有步骤待执行"""
    plan = state.get("plan", {})
    total = len(plan.get("steps", []))
    current = state.get("current_step", 0)
    return "summarize" if current >= total else "execute"


def build_plan_execute_graph():
    """构建 Plan-then-Execute 的 LangGraph 图"""
    builder = StateGraph(AgentState)
    builder.add_node("plan", plan_node)
    builder.add_node("execute", execute_node)
    builder.add_node("summarize", summarize_node)
    builder.set_entry_point("plan")
    builder.add_edge("plan", "execute")
    builder.add_conditional_edges("execute", should_continue, {"execute": "execute", "summarize": "summarize"})
    builder.add_edge("summarize", END)
    return builder.compile(checkpointer=MemorySaver())
