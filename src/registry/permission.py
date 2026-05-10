from src.config import settings


def is_allowed(module_name: str) -> bool:
    """检查模块是否启用（基于 .env 配置）"""
    key = f"TOOL_{module_name.upper()}"
    return getattr(settings, key.lower(), "true") == "true"
