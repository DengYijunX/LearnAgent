import json
from langchain_core.messages import SystemMessage, HumanMessage
from src.llm import get_llm
from src.models.schemas import UserInput, RouterDecision, TaskType
from src.logging_config import setup_logging

logger = setup_logging()

ROUTER_PROMPT = """你是一个任务路由器。判断用户输入属于哪种类型：

- **simple**：问概念、查资料、解释名词、搜索文档。只需搜索+总结。
- **complex**：表达"我要学X"、"帮我掌握X"、"带我做X项目"等学习意图。需要生成教学项目。

只返回 JSON：
{"task_type": "simple|complex", "reason": "一句话说明判断依据"}"""


async def route_task(user_input: UserInput) -> RouterDecision:
    """LLM 驱动的任务路由"""
    logger.debug("router 开始", query=user_input.query[:100])
    try:
        llm = get_llm(model="simple", max_tokens=200)
        msgs = [
            SystemMessage(content=ROUTER_PROMPT),
            HumanMessage(content=user_input.query),
        ]
        response = await llm.ainvoke(msgs)
        content = response.content.strip()
        # 提取 JSON（兼容 LLM 可能包裹 ```json 的情况）
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)
        decision = RouterDecision(
            task_type=TaskType(data["task_type"]),
            reason=data.get("reason", ""),
        )
        logger.info("router 决策完成", query=user_input.query[:50], task_type=decision.task_type.value)
        return decision
    except Exception as e:
        logger.error("router 失败，降级为 simple", query=user_input.query[:50], error=str(e))
        return RouterDecision(task_type=TaskType.SIMPLE, reason="router fallback due to error")
