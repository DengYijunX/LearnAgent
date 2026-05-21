"""Manual smoke test for the real DeepSeek LLM client."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.config.settings import load_settings
from app.llm.base import LLMRequest
from app.llm.deepseek_client import DeepSeekLLMClient
from app.llm.model_selector import ModelSelector


async def main() -> int:
    settings = load_settings()
    if not settings.run_real_tests and os.getenv("RUN_REAL_TESTS") != "1":
        print("跳过真实 LLM smoke test：请设置 RUN_REAL_TESTS=1。")
        return 0

    client = DeepSeekLLMClient(
        settings=settings,
        model_selector=ModelSelector(settings),
    )
    response = await client.chat(
        LLMRequest(
            messages=[
                {
                    "role": "user",
                    "content": "用一句话说明 LearnAgent 是什么。",
                }
            ],
            mode=settings.model_mode,
            max_tokens=128,
        )
    )
    print(response.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
