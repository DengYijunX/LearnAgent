"""DeepSeek API 连通性冒烟测试。

使用方式：
    python scripts/smoke_llm_real.py

前提条件：
    1. 已复制 .env.example 为 .env
    2. 已填写 DEEPSEEK_API_KEY
    3. 已安装 httpx（pip install httpx python-dotenv）
"""

import asyncio
import os
import sys

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import get_config


async def main():
    cfg = get_config()

    if not cfg.api_key:
        print("错误：未设置 DEEPSEEK_API_KEY。请在 .env 中配置。")
        sys.exit(1)

    from app.llm.deepseek_client import DeepSeekLLMClient

    print(f"服务商：DeepSeek")
    print(f"Base URL：{cfg.base_url}")
    print(f"小模型：{cfg.small_model}")
    print(f"大模型：{cfg.large_model}")
    print()

    # 测试小模型
    print(f"[1/2] 测试小模型 ({cfg.small_model})...")
    try:
        client = DeepSeekLLMClient(
            api_key=cfg.api_key,
            base_url=cfg.base_url,
            model=cfg.small_model,
        )
        result = await client.chat(
            messages=[{"role": "user", "content": "用一句话介绍 Python。"}],
        )
        content = result.get("content", "")
        print(f"  响应：{content[:100]}...")
        print(f"  小模型测试通过 ✓\n")
    except Exception as e:
        print(f"  小模型测试失败 ✗：{e}\n")

    # 测试大模型
    print(f"[2/2] 测试大模型 ({cfg.large_model})...")
    try:
        client = DeepSeekLLMClient(
            api_key=cfg.api_key,
            base_url=cfg.base_url,
            model=cfg.large_model,
        )
        result = await client.chat(
            messages=[{"role": "user", "content": "1+1=?"}],
        )
        content = result.get("content", "")
        print(f"  响应：{content[:100]}...")
        print(f"  大模型测试通过 ✓\n")
    except Exception as e:
        print(f"  大模型测试失败 ✗：{e}\n")

    print("冒烟测试完成。")


if __name__ == "__main__":
    asyncio.run(main())
