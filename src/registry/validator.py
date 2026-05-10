from src.config import settings
from src.logging_config import setup_logging

logger = setup_logging()

_REQUIRED = {
    "llm_api_key": settings.anthropic_api_key or settings.deepseek_api_key or settings.openai_api_key or settings.llm_api_key,
}


def validate_config(strict: bool = False):
    """启动时校验必填配置。strict=False 只 warning，strict=True 抛异常。"""
    provider = settings.llm_provider
    key_map = {
        "anthropic": settings.anthropic_api_key,
        "deepseek": settings.deepseek_api_key,
        "openai": settings.openai_api_key,
    }
    api_key = key_map.get(provider) or settings.llm_api_key

    issues = []

    if not api_key:
        msg = f"缺少 LLM API Key: LLM_PROVIDER={provider}，请设置对应 {provider.upper()}_API_KEY"
        issues.append(msg)

    if not settings.tavily_api_key:
        issues.append("TAVILY_API_KEY 未设置，web_search 将不可用")

    for issue in issues:
        if strict:
            raise ValueError(issue)
        logger.warning(issue)

    return len(issues) == 0
