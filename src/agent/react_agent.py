import json
from langchain_core.messages import SystemMessage, HumanMessage
from src.llm import get_llm
from src.models.schemas import KnowledgeSummary
from src.tools.web_search import web_search
from src.tools.content_fetch import fetch_content
from src.logging_config import setup_logging

logger = setup_logging()

DECIDE_PROMPT = """你判断是否需要联网搜索来回答用户问题。

- 如果你已有的知识足以给出准确回答 → action: "answer"
- 如果问题涉及最新信息、需要查资料、或你不确定 → action: "search"

只返回 JSON：
{"action": "answer|search", "reason": "一句话"}"""

KNOWLEDGE_PROMPT = """你是一个知识助手。用你的已有知识回答用户问题。

要求：
1. 给出准确、有用的回答
2. 如果答案涉及技术概念，提炼核心概念（core_concepts）
3. 如果适用，列出学习要点（learning_points）
4. 如果适用，列出相关技术（related_techs）
5. topic 用用户问题的主题

只返回 JSON：
{"topic": "主题", "core_concepts": [...], "learning_points": [...], "related_techs": [...]}"""

SEARCH_PROMPT = """你是一个技术学习助手。根据以下搜索资料，为用户总结知识点。

要求：
1. 提炼核心概念（core_concepts）
2. 列出学习要点（learning_points），按入门到深入排列
3. 列出相关技术（related_techs）

只返回 JSON：
{"topic": "技术名", "core_concepts": [...], "learning_points": [...], "related_techs": [...]}"""


async def _parse_llm_json(model: str, system: str, user: str, max_tokens: int = 1000) -> dict:
    llm = get_llm(model=model, max_tokens=max_tokens)
    msgs = [SystemMessage(content=system), HumanMessage(content=user)]
    response = await llm.ainvoke(msgs)
    content = response.content.strip()
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content)


async def run_react_agent(query: str, memory_manager=None) -> KnowledgeSummary:
    """ReAct 循环：决定是否搜索 → 搜索(可选) → 阅读(可选) → 总结"""
    logger.info("ReAct agent 启动", query=query[:100])

    has_search_context = False
    combined_content = ""

    # Step 1: Decide — 是否真的需要搜索
    try:
        decision = await _parse_llm_json("simple", DECIDE_PROMPT, query, max_tokens=100)
        should_search = decision.get("action") == "search"
        logger.debug("ReAct 决策", action=decision.get("action"), reason=decision.get("reason"))
    except Exception:
        should_search = True  # 决策失败时默认搜索

    # Step 2: Search（仅在需要时）
    if should_search:
        search_results = await web_search(query)
        logger.debug("ReAct 搜索完成", count=len(search_results))

        # Step 3: Read（仅在搜索有结果时，取前 1-2 个）
        if search_results:
            contents = []
            for r in search_results[:2]:
                fetched = await fetch_content(r["url"])
                if fetched.content:
                    contents.append(fetched.content[:5000])
            combined_content = "\n\n---\n\n".join(contents)
            has_search_context = bool(combined_content.strip())

    # Step 4: Answer
    try:
        if has_search_context:
            data = await _parse_llm_json(
                "simple", SEARCH_PROMPT,
                f"用户查询：{query}\n\n搜索资料：{combined_content[:8000]}",
            )
        else:
            data = await _parse_llm_json(
                "simple", KNOWLEDGE_PROMPT,
                f"用户查询：{query}",
            )

        result = KnowledgeSummary(**data)

        if memory_manager and result.topic:
            try:
                memory_manager.save_learning(result.topic, result)
                memory_manager.update_profile(result.topic)
                if has_search_context:
                    memory_manager.write_artifact(result.topic, result)
            except Exception as e:
                logger.warning("Memory auto-save failed", error=str(e))

        return result
    except Exception as e:
        logger.error("ReAct 总结失败", error=str(e))
        return KnowledgeSummary(topic=query, learning_points=["总结失败，请重试"])
