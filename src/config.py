from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    anthropic_model_simple: str = "claude-sonnet-4-6"
    anthropic_model_complex: str = "claude-opus-4-7"

    tavily_api_key: str = ""
    jina_api_key: str = ""
    github_token: str = ""

    slack_webhook_url: str = ""

    log_level: str = "DEBUG"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
