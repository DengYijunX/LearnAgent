from src.registry.permission import is_allowed
from src.logging_config import setup_logging

logger = setup_logging()


class ModuleInfo:
    def __init__(self, name: str, category: str, description: str = "",
                 provider: str = "", risk: str = "low", extra: dict | None = None):
        self.name = name
        self.category = category
        self.description = description
        self.provider = provider
        self.risk = risk
        self.extra = extra or {}

    @property
    def enabled(self) -> bool:
        return is_allowed(self.name)

    @property
    def status_text(self) -> str:
        return "✓" if self.enabled else "✗"


class Registry:
    """只读控制面：展示模块状态，不执行工具。"""
    def __init__(self):
        self._modules: dict[str, ModuleInfo] = {}

    def register(self, name: str, category: str, description: str = "",
                 provider: str = "", risk: str = "low", extra: dict | None = None):
        self._modules[name] = ModuleInfo(name, category, description, provider, risk, extra)

    def status(self) -> list[dict]:
        rows = []
        for mod in self._modules.values():
            rows.append({
                "name": mod.name,
                "category": mod.category,
                "enabled": mod.enabled,
                "provider": mod.provider,
                "risk": mod.risk,
            })
        return rows

    def status_text(self) -> str:
        lines = []
        cats: dict[str, list[ModuleInfo]] = {}
        for m in self._modules.values():
            cats.setdefault(m.category, []).append(m)

        for cat, mods in cats.items():
            lines.append(f"\n{cat}")
            for m in mods:
                provider_info = f" | provider={m.provider}" if m.provider else ""
                extra_info = ""
                if m.extra:
                    for k, v in m.extra.items():
                        extra_info += f" | {k}={v}"
                lines.append(f"  {m.name:18} {m.status_text} {provider_info} | risk={m.risk}{extra_info}")

        lines.append("")
        return "\n".join(lines)


_registry = Registry()


def get_registry() -> Registry:
    return _registry
