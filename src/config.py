from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM provider: anthropic | deepseek | openai
    llm_provider: str = "anthropic"
    # 通用 API Key（优先级低于 provider 专属 key）
    llm_api_key: str = ""
    # OpenAI 兼容 API 的 base_url（DeepSeek 等需要）
    llm_base_url: str = ""
    # 模型名（按复杂度分两档）
    llm_model_simple: str = ""
    llm_model_complex: str = ""

    # Provider 专属 Key（兼容旧配置）
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    openai_api_key: str = ""

    # 外部工具
    tavily_api_key: str = ""
    jina_api_key: str = ""
    github_token: str = ""

    # 通知
    slack_webhook_url: str = ""

    # 日志
    log_level: str = "DEBUG"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
