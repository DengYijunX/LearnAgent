"""SWE 功能测试：用真实 API 问软件工程问题。

用法：
    python scripts/test_swe_real.py
"""

import asyncio
import io
import os
import sys
import time

# Windows GBK 终端兼容
if sys.stdout.encoding and sys.stdout.encoding.lower() in ("gbk", "gb2312", "gb18030"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import get_config
from app.llm.deepseek_client import DeepSeekLLMClient
from app.llm.model_selector import ModelSelector
from app.tools.registry import ToolRegistry
from app.tools.search_web import RealSearchWeb
from app.tools.read_url import RealReadUrl
from app.tools.github_analyzer import RealGitHubAnalyzer
from app.tools.workspace_tools import FileWrite, FileRead, RunCode, ListFiles
from app.tools.todo_tools import LearningTodoWrite
from app.core.query_engine import LearnQueryEngine
from app.memory.session_store import SessionStore
from app.memory.memory_store import MemoryStore


# ─── SWE 测试问题集 ──────────────────────────────────────────────

SWE_QUESTIONS = [
    {
        "id": "code_review",
        "question": "帮我审查这段 Python 代码有什么问题：\n\n"
                    "def get_user(user_id, db):\n"
                    "    query = f\"SELECT * FROM users WHERE id = {user_id}\"\n"
                    "    result = db.execute(query)\n"
                    "    return result.fetchone()\n\n"
                    "data = get_user(request.GET['id'], db)\n"
                    "if data:\n"
                    "    return {'name': data[1], 'email': data[2]}",
    },
    {
        "id": "debugging",
        "question": "下面这段代码会报错，帮我分析原因并修复：\n\n"
                    "import asyncio\n\n"
                    "async def fetch_data(url):\n"
                    "    return f\"data from {url}\"\n\n"
                    "urls = ['a.com', 'b.com', 'c.com']\n"
                    "results = [fetch_data(u) for u in urls]\n"
                    "print(results)",
    },
    {
        "id": "architecture",
        "question": "对比 FastAPI 和 Flask 的设计哲学，在什么场景下应该选择 FastAPI 而不是 Flask？",
    },
    {
        "id": "code_gen",
        "question": "帮我写一个 Python 装饰器，用来统计函数执行时间，并支持可选的自定义标签参数。",
    },
    {
        "id": "learn_concept",
        "question": "我想学习 Git 的 rebase 和 merge 的区别，能解释一下吗？",
    },
]


async def main():
    cfg = get_config()

    if not cfg.api_key:
        print("❌ 错误：未设置 DEEPSEEK_API_KEY。请在 .env 中配置。")
        sys.exit(1)

    print("=" * 60)
    print("  LearnAgent SWE 功能测试")
    print(f"  模型: {cfg.small_model} (小型) / {cfg.large_model} (大型)")
    print(f"  模式: {cfg.model_mode}")
    print("=" * 60)
    print()

    # 初始化组件
    storage_base = cfg.storage_base_dir
    session_store = SessionStore(base_dir=os.path.join(storage_base, "sessions"))
    memory_store = MemoryStore(base_dir=os.path.join(storage_base, "memory"))

    tools = ToolRegistry()
    tools.register(RealSearchWeb(max_results=5))
    tools.register(RealReadUrl(timeout=15))
    tools.register(RealGitHubAnalyzer(timeout=20))
    tools.register(LearningTodoWrite())

    workspace_dir = os.path.join(storage_base, "workspace", "_swe_test")
    os.makedirs(workspace_dir, exist_ok=True)
    tools.register(FileWrite(workspace_root=workspace_dir))
    tools.register(FileRead(workspace_root=workspace_dir))
    tools.register(RunCode(workspace_root=workspace_dir, timeout=30))
    tools.register(ListFiles(workspace_root=workspace_dir))

    selector = ModelSelector(cfg.small_model, cfg.large_model)
    llm = DeepSeekLLMClient(
        api_key=cfg.api_key or "",
        base_url=cfg.base_url,
        model=selector.select(cfg.model_mode),
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
    )

    engine = LearnQueryEngine(
        llm=llm,
        tools=tools,
        session_store=session_store,
        memory_store=memory_store,
        skills_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills"),
    )

    # 运行测试
    passed = 0
    failed = 0

    for i, q in enumerate(SWE_QUESTIONS, 1):
        print(f"\n{'─' * 60}")
        print(f"  测试 {i}/{len(SWE_QUESTIONS)}: {q['id']}")
        print(f"  Q: {q['question'][:80]}...")
        print(f"{'─' * 60}")

        t0 = time.time()
        try:
            result = await engine.submit_message(q["question"])
            elapsed = time.time() - t0

            # 提取回复
            content = None
            for m in reversed(result.get("messages", [])):
                if m.get("role") == "assistant" and m.get("content"):
                    content = m["content"]
                    break

            if content:
                # 截取前 200 字展示
                preview = content[:200].replace("\n", " ")
                print(f"\n  🤖 {preview}...")
                print(f"\n  ✅ 完成 ({elapsed:.1f}s)")
                passed += 1
            else:
                print(f"\n  ⚠️  未获取到回复内容")
                failed += 1
        except Exception as e:
            elapsed = time.time() - t0
            print(f"\n  ❌ 错误: {e} ({elapsed:.1f}s)")
            failed += 1

    # 汇总
    print(f"\n{'=' * 60}")
    print(f"  SWE 测试完成")
    print(f"  通过: {passed}/{len(SWE_QUESTIONS)}")
    print(f"  失败: {failed}/{len(SWE_QUESTIONS)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
