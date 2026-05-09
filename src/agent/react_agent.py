import json
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import settings
from src.models.schemas import KnowledgeSummary
from src.tools.web_search import web_search
from src.tools.content_fetch import fetch_content
from src.logging_config import setup_logging

logger = setup_logging()

SUMMARIZE_PROMPT = """你是一个技术学习助手。根据以下搜索资料，为用户总结技术知识点。

要求：
1. 提炼核心概念（core_concepts）
2. 列出学习要点（learning_points），按入门到深入排列
3. 列出相关技术（related_techs）

只返回 JSON：
{"topic": "技术名", "core_concepts": [...], "learning_points": [...], "related_techs": [...]}"""


async def run_react_agent(query: str) -> KnowledgeSummary:
    """ReAct 循环：搜索 → 阅读最佳结果 → LLM 提炼总结"""
    logger.info("ReAct agent 启动", query=query[:100])

    # Step 1: Search
    search_results = await web_search(query)
    logger.debug("ReAct 搜索完成", count=len(search_results))

    # Step 2: Read（取前 2 个结果的内容）
    contents = []
    for r in search_results[:2]:
        fetched = await fetch_content(r["url"])
        if fetched.content:
            contents.append(fetched.content[:5000])
    combined_content = "\n\n---\n\n".join(contents)

    # Step 3: Summarize
    try:
        llm = ChatAnthropic(
            model=settings.anthropic_model_simple,
            api_key=settings.anthropic_api_key,
            max_tokens=1000,
        )
        msgs = [
            SystemMessage(content=SUMMARIZE_PROMPT),
            HumanMessage(content=f"用户查询：{query}\n\n搜索资料：{combined_content[:8000] or '未找到相关资料'}"),
        ]
        response = await llm.ainvoke(msgs)
        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)
        return KnowledgeSummary(**data)
    except Exception as e:
        logger.error("ReAct 总结失败", error=str(e))
        return KnowledgeSummary(topic=query, learning_points=["总结失败，请重试"])
