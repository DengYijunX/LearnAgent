"""Quick LLM Router test (run directly, not via bash pipe)."""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config.settings import get_config
from app.llm.deepseek_client import DeepSeekLLMClient
from app.core.llm_router import LLMRouter

async def main():
    cfg = get_config()
    llm = DeepSeekLLMClient(api_key=cfg.api_key or '', base_url=cfg.base_url, model=cfg.small_model, temperature=0.2, max_tokens=2048)
    router = LLMRouter(llm)
    cases = [
        '我想学习 Rust 的 async await',
        '讲讲 tokio 怎么用',
        '继续',
        '装饰器那个例子跑一下',
    ]
    import time
    for q in cases:
        t0 = time.time()
        r = await router.route(q)
        t = time.time() - t0
        print(f'"{q}" -> intent={r["intent"]} topic={r["topic"]} ({t:.1f}s)')

asyncio.run(main())
