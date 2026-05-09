import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.config import settings
from src.logging_config import setup_logging

logger = setup_logging()

scheduler = AsyncIOScheduler()


async def send_slack_message(text: str) -> bool:
    """通过 Slack Webhook 发送消息"""
    if not settings.slack_webhook_url:
        logger.warning("Slack Webhook 未配置")
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                settings.slack_webhook_url,
                json={"text": text},
            )
            resp.raise_for_status()
            logger.info("Slack 消息已发送", text=text[:50])
            return True
    except Exception as e:
        logger.error("Slack 发送失败", error=str(e))
        return False


async def daily_push_callback():
    """每日定时推送：搜索 AI Agent 最新动态并发送"""
    from src.tools.web_search import web_search
    logger.info("定时推送触发")
    results = await web_search("AI Agent 最新进展 2026", max_results=3)
    if not results:
        await send_slack_message("📚 今日 AI Agent 学习推荐：暂无新内容")
        return
    lines = ["📚 今日 AI Agent 学习推荐："]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. *{r['title']}* — {r['url']}")
        lines.append(f"   {r['content'][:120]}...")
    await send_slack_message("\n".join(lines))


def start_scheduler(hour: int = 9, minute: int = 0):
    """启动定时调度器：每天 9 点推送"""
    from apscheduler.triggers.cron import CronTrigger
    scheduler.add_job(
        daily_push_callback,
        CronTrigger(hour=hour, minute=minute),
        id="daily_push",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("定时调度器已启动", time=f"{hour:02d}:{minute:02d}")
