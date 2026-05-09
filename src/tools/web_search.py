import httpx
from src.config import settings
from src.logging_config import setup_logging

logger = setup_logging()

TAVILY_API_URL = "https://api.tavily.com/search"


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    使用 Tavily API 搜索技术资料。
    返回: [{"title": ..., "url": ..., "content": ...}, ...]
    """
    if not query.strip():
        logger.warning("web_search: 空查询")
        return []

    logger.debug("web_search 开始", query=query)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                TAVILY_API_URL,
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            logger.info("web_search 完成", query=query, result_count=len(results))
            return [
                {"title": r["title"], "url": r["url"], "content": r["content"]}
                for r in results
            ]
    except Exception as e:
        logger.error("web_search 失败", query=query, error=str(e))
        return []
