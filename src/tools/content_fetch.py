import httpx
from pydantic import BaseModel
from src.config import settings
from src.logging_config import setup_logging

logger = setup_logging()


class FetchedContent(BaseModel):
    url: str = ""
    title: str = ""
    content: str = ""


async def fetch_content(url: str) -> FetchedContent:
    """使用 Jina AI Reader 抓取网页内容转 Markdown。降级方案：直接用 httpx 抓取。"""
    if not url.strip():
        return FetchedContent()

    logger.debug("fetch_content 开始", url=url)
    try:
        jina_url = f"https://r.jina.ai/{url}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                jina_url,
                headers={"Authorization": f"Bearer {settings.jina_api_key}"}
                if settings.jina_api_key else {},
            )
            resp.raise_for_status()
            logger.info("fetch_content 完成", url=url, length=len(resp.text))
            return FetchedContent(url=url, content=resp.text)
    except Exception:
        # 降级：直接抓取 HTML
        logger.warning("Jina Reader 失败，降级为直接抓取", url=url)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, headers={"User-Agent": "LearnAgent/1.0"})
                resp.raise_for_status()
                return FetchedContent(url=url, content=resp.text[:10000])
        except Exception as e:
            logger.error("fetch_content 失败", url=url, error=str(e))
            return FetchedContent(url=url, content="")
