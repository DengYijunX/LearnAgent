import asyncio
import sys
from fastapi import FastAPI
from src.logging_config import setup_logging
from src.models.schemas import UserInput, TaskType
from src.router.router import route_task
from src.agent.react_agent import run_react_agent

logger = setup_logging()
app = FastAPI(title="LearnAgent", version="0.1.0")

_memory_manager = None


def _get_memory():
    global _memory_manager
    if _memory_manager is None:
        try:
            from src.memory.memory_manager import MemoryManager
            _memory_manager = MemoryManager()
        except Exception as e:
            logger.warning("Memory init failed", error=str(e))
    return _memory_manager


@app.on_event("startup")
async def startup():
    global _memory_manager
    _memory_manager = _get_memory()
    from src.tools.notify import start_scheduler
    start_scheduler()
    logger.info("LearnAgent 启动完成")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/learn")
async def learn(user_input: UserInput):
    logger.info("API learn 请求", query=user_input.query[:50])
    mgr = _get_memory()
    decision = await route_task(user_input)
    if decision.task_type == TaskType.COMPLEX:
        from src.agent.plan_execute_agent import build_plan_execute_graph
        from src.memory.working import create_initial_state
        graph = build_plan_execute_graph(memory_manager=mgr)
        state = create_initial_state(user_input.query)
        config = {"configurable": {"thread_id": "learn-session"}}
        messages = []
        async for event in graph.astream(state, config):
            for _, node_output in event.items():
                msgs = node_output.get("messages", [])
                messages.extend(msgs)
        return {"task_type": "complex", "messages": messages, "reason": decision.reason}
    result = await run_react_agent(user_input.query, memory_manager=mgr)
    return {"task_type": "simple", "result": result.model_dump()}


def _print_result(result):
    print(f"\n📖 {result.topic}")
    print(f"核心概念: {', '.join(result.core_concepts) if result.core_concepts else '无'}")
    print("学习要点:")
    for i, point in enumerate(result.learning_points, 1):
        print(f"  {i}. {point}")
    print(f"相关技术: {', '.join(result.related_techs) if result.related_techs else '无'}")


def _handle_command(cmd: str, mgr) -> bool:
    """处理 CLI 命令。返回 True 表示已处理。"""
    if cmd == "/quit":
        raise EOFError

    if cmd == "/status":
        print("\n📊 模块状态")
        print("🧠 核心层")
        print("  Router         ✓ | LLM: deepseek-v4-flash")
        print("  ReAct          ✓ | 搜索→抓取→总结")
        print("  Plan-Execute   ✓ | LangGraph 图式编排")
        print("\n📦 记忆层")
        if mgr:
            recent = mgr.get_recent(limit=5)
            print(f"  学习记录       ✓ | {len(recent)} 条")
            print(f"  用户画像       ✓ | {mgr.get_profile_summary()}")
        else:
            print("  记忆层         ✗ | 未初始化")
        print("\n💾 会话日志")
        print("  sessions       ✓ | data/sessions/")
        print("\n📄 Artifact")
        print("  summaries      ✓ | artifacts/")
        print("  projects       ✓ | artifacts/")
        return True

    if cmd == "/history":
        print("")
        if not mgr:
            print("记忆层未初始化")
            return True
        recent = mgr.get_recent(10)
        if recent:
            print("📚 最近学习:")
            for r in recent:
                print(f"  - {r['topic']} ({r.get('created_at', '')[:10]})")
        else:
            print("📚 暂无学习记录")
        return True

    if cmd == "/profile":
        print("")
        if mgr:
            print("👤 " + mgr.get_profile_summary())
        return True

    if cmd.startswith("/memory "):
        keyword = cmd[len("/memory "):].strip()
        print("")
        if not mgr:
            print("记忆层未初始化")
            return True
        results = mgr.search_memory(keyword, limit=5)
        if results:
            print(f"🔍 搜索 '{keyword}' 的结果:")
            for r in results:
                print(f"  - {r['topic']} ({r.get('created_at', '')[:10]}) [相关度: {r.get('score', 0)}]")
        else:
            print(f"🔍 未找到与 '{keyword}' 相关的记忆")
        return True

    return False


async def cli_main():
    logger.info("LearnAgent CLI 启动")
    mgr = _get_memory()

    print("=" * 50)
    print("LearnAgent - AI 学习助手")
    print("=" * 50)

    if mgr:
        recent = mgr.get_recent(5)
        if recent:
            print("\n📚 最近学习:")
            for r in recent:
                print(f"  - {r['topic']} ({r.get('created_at', '')[:10]})")
        print(f"\n👤 {mgr.get_profile_summary()}")

    print("\n命令: /quit 退出 | /status 状态 | /history 历史 | /profile 画像 | /memory <关键词> 搜索")
    print("直接输入技术名开始学习")

    while True:
        try:
            query = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query:
            continue

        if query.startswith("/"):
            try:
                _handle_command(query, mgr)
            except EOFError:
                break
            continue

        if mgr:
            mgr.log("user_input", {"query": query})

        decision = await route_task(UserInput(query=query))
        print(f"[路由] {decision.task_type.value} — {decision.reason}")

        if decision.task_type == TaskType.COMPLEX:
            from src.agent.plan_execute_agent import build_plan_execute_graph
            from src.memory.working import create_initial_state
            graph = build_plan_execute_graph(memory_manager=mgr)
            state = create_initial_state(query)
            config = {"configurable": {"thread_id": "learn-session"}}
            async for event in graph.astream(state, config):
                for _, node_output in event.items():
                    msgs = node_output.get("messages", [])
                    for m in msgs:
                        print(f"\n{m['content']}")
            continue

        result = await run_react_agent(query, memory_manager=mgr)
        _print_result(result)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        import uvicorn
        from src.tools.notify import start_scheduler
        start_scheduler()
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        asyncio.run(cli_main())
