import asyncio
import sys
from fastapi import FastAPI
from src.config import settings
from src.logging_config import setup_logging
from src.models.schemas import UserInput
from src.router.router import route_task
from src.agent.react_agent import run_react_agent
from src.models.schemas import TaskType

logger = setup_logging()
app = FastAPI(title="LearnAgent", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/learn")
async def learn(user_input: UserInput):
    """学习接口：输入技术名，返回知识总结"""
    logger.info("API learn 请求", query=user_input.query[:50])
    decision = await route_task(user_input)
    if decision.task_type == TaskType.COMPLEX:
        return {"task_type": "complex", "message": "复杂任务支持将在 P1 阶段实现", "reason": decision.reason}
    result = await run_react_agent(user_input.query)
    return {"task_type": "simple", "result": result.model_dump()}


async def cli_main():
    """CLI 入口"""
    logger.info("LearnAgent CLI 启动")
    print("=" * 50)
    print("LearnAgent - AI 学习助手")
    print("输入 '/quit' 退出，输入技术名开始学习")
    print("=" * 50)

    while True:
        try:
            query = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query:
            continue
        if query == "/quit":
            break

        decision = await route_task(UserInput(query=query))
        print(f"[路由] {decision.task_type.value} — {decision.reason}")

        if decision.task_type == TaskType.COMPLEX:
            print("(复杂任务将在 P1 阶段支持)")
            continue

        result = await run_react_agent(query)
        print(f"\n📖 {result.topic}")
        print(f"核心概念: {', '.join(result.core_concepts) if result.core_concepts else '无'}")
        print(f"学习要点:")
        for i, point in enumerate(result.learning_points, 1):
            print(f"  {i}. {point}")
        print(f"相关技术: {', '.join(result.related_techs) if result.related_techs else '无'}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        asyncio.run(cli_main())
