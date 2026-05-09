from langchain_core.language_models import BaseChatModel
from src.config import settings
from src.logging_config import setup_logging

logger = setup_logging()

# 默认模型
_DEFAULTS = {
    "anthropic": {
        "simple": "claude-sonnet-4-6",
        "complex": "claude-opus-4-7",
        "base_url": "",
    },
    "deepseek": {
        "simple": "deepseek-chat",
        "complex": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
    },
    "openai": {
        "simple": "gpt-4o",
        "complex": "gpt-4o",
        "base_url": "",
    },
}


def _resolve_api_key() -> str:
    """解析 API Key：provider 专属 key > 通用 key"""
    key_map = {
        "anthropic": settings.anthropic_api_key,
        "deepseek": settings.deepseek_api_key,
        "openai": settings.openai_api_key,
    }
    return key_map.get(settings.llm_provider, "") or settings.llm_api_key


def get_llm(model: str = "simple", max_tokens: int = 1000) -> BaseChatModel:
    """
    LLM 工厂。根据 LLM_PROVIDER 返回对应的模型实例。

    Args:
        model: "simple" | "complex"
        max_tokens: 最大输出 token
    """
    provider = settings.llm_provider.lower()
    api_key = _resolve_api_key()
    defaults = _DEFAULTS.get(provider, {})

    model_name = (
        settings.llm_model_simple if model == "simple" else settings.llm_model_complex
    ) or defaults.get(model, "")

    base_url = settings.llm_base_url or defaults.get("base_url", "")

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        logger.debug("创建 ChatAnthropic", model=model_name)
        return ChatAnthropic(
            model=model_name,
            api_key=api_key,
            max_tokens=max_tokens,
        )

    # OpenAI 兼容协议（DeepSeek、OpenAI 等）
    from langchain_openai import ChatOpenAI
    kwargs = {
        "model": model_name,
        "api_key": api_key,
        "max_tokens": max_tokens,
    }
    if base_url:
        kwargs["base_url"] = base_url

    logger.debug("创建 ChatOpenAI", model=model_name, base_url=base_url)
    return ChatOpenAI(**kwargs)
