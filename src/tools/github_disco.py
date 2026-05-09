import httpx
from src.config import settings
from src.logging_config import setup_logging

logger = setup_logging()

GITHUB_API = "https://api.github.com"


async def search_github_repos(query: str, per_page: int = 5) -> list[dict]:
    """搜索 GitHub 仓库"""
    if not query.strip():
        return []

    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    logger.debug("github_search 开始", query=query)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{GITHUB_API}/search/repositories",
                params={"q": query, "sort": "stars", "per_page": per_page},
                headers=headers,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            logger.info("github_search 完成", query=query, count=len(items))
            return [
                {
                    "full_name": item["full_name"],
                    "description": item.get("description", ""),
                    "html_url": item["html_url"],
                    "stargazers_count": item.get("stargazers_count", 0),
                    "language": item.get("language", ""),
                }
                for item in items
            ]
    except Exception as e:
        logger.error("github_search 失败", query=query, error=str(e))
        return []


async def get_github_trending(language: str = "") -> list[dict]:
    """获取 GitHub Trending（按今日创建时间排序的仓库）"""
    q = f"created:>$(date -d '7 days ago' +%Y-%m-%d)"
    if language:
        q += f" language:{language}"
    return await search_github_repos(q)
