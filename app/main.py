"""LearnAgent CLI 入口。

使用方式：
    python -m app.main              # 使用 MockLLMClient + Mock 工具（无需 API key）
    python -m app.main --real       # 使用 DeepSeek API（需要 .env 配置）
"""

import asyncio
import sys

from app.config.settings import get_config
from app.llm.mock_client import MockLLMClient
from app.llm.model_selector import ModelSelector
from app.tools.registry import ToolRegistry
from app.tools.search_web import MockSearchWeb, RealSearchWeb
from app.tools.read_url import MockReadUrl, RealReadUrl
from app.tools.todo_tools import LearningTodoWrite
from app.core.router import InputRouter
from app.core.query_engine import LearnQueryEngine


def build_engine(use_real: bool = False):
    cfg = get_config()

    # 工具注册
    tools = ToolRegistry()
    if use_real:
        tools.register(RealSearchWeb(max_results=5))
        tools.register(RealReadUrl(timeout=15))
    else:
        tools.register(MockSearchWeb())
        tools.register(MockReadUrl())
    tools.register(LearningTodoWrite())

    # LLM 客户端
    if use_real:
        from app.llm.deepseek_client import DeepSeekLLMClient

        selector = ModelSelector(cfg.small_model, cfg.large_model)
        model = selector.select(cfg.model_mode)
        llm = DeepSeekLLMClient(
            api_key=cfg.api_key or "",
            base_url=cfg.base_url,
            model=model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
    else:
        llm = MockLLMClient()

    return LearnQueryEngine(llm=llm, tools=tools)


async def main():
    use_real = "--real" in sys.argv
    engine = build_engine(use_real=use_real)
    router = InputRouter()

    mode = "真实 API (DeepSeek)" if use_real else "Mock 模式"
    print(f"LearnAgent v0.1.0 | {mode}")
    print(f"已注册工具：{', '.join(engine.tools._tools.keys())}")
    print("输入 /help 查看命令，/exit 退出\n")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        # Router 识别意图
        route = router.route(user_input)
        intent = route["intent"]
        topic = route.get("topic")

        if not user_input.startswith("/"):
            print(f"[Router] intent={intent} topic={topic}")

        result = await engine.submit_message(user_input, topic=topic, intent=intent)

        if result.get("type") == "command":
            msg = result.get("content", "")
            print(msg)
            if user_input.startswith("/exit"):
                break
        else:
            messages = result.get("messages", [])
            last = messages[-1] if messages else {}
            content = last.get("content", "(无输出)")
            print(f"\n{content}\n")


if __name__ == "__main__":
    asyncio.run(main())
