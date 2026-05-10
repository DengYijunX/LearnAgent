class ToolError(Exception):
    pass


class ConfigError(ToolError):
    pass


class ProviderError(ToolError):
    pass
