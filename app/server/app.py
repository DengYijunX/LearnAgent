"""FastAPI application factory for LearnAgent web server."""

import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded .env file successfully")
except ImportError:
    logger.warning("python-dotenv not installed, skipping .env load")
except Exception as e:
    logger.error(f"Failed to load .env file: {e}")

from .session_manager import SessionManager
from .routes import router as api_router

# 导入 Agent 核心模块
from app.context.context_builder import build_system_prompt
from app.llm.deepseek_client import DeepSeekLLMClient
from app.tools.registry import ToolRegistry
from app.tools.search_web import RealSearchWeb
from app.tools.read_url import RealReadUrl
from app.tools.workspace_tools import FileWrite, FileRead, RunCode, ListFiles
from app.tools.todo_tools import LearningTodoWrite
from app.core.agent_loop import agent_loop
from app.core.llm_router import LLMRouter
from app.core.query_engine import INTENT_TO_SKILL
from app.memory.memory_store import MemoryStore


# 全局变量
_session_manager: Optional[SessionManager] = None
_llm_client: Optional[DeepSeekLLMClient] = None
_tool_registry: Optional[ToolRegistry] = None
_memory_store: Optional[MemoryStore] = None


def get_session_manager() -> SessionManager:
    assert _session_manager is not None
    return _session_manager


def get_llm_client() -> DeepSeekLLMClient:
    assert _llm_client is not None
    return _llm_client


def get_tool_registry() -> ToolRegistry:
    assert _tool_registry is not None
    return _tool_registry


def _create_llm_client() -> DeepSeekLLMClient:
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    model = os.getenv("DEEPSEEK_SMALL_MODEL", "deepseek-chat")

    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY environment variable is not set")

    return DeepSeekLLMClient(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0.2,
        max_tokens=2048,
    )


def _create_tool_registry() -> ToolRegistry:
    workspace_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../storage/workspace")
    )

    registry = ToolRegistry()
    registry.register(RealSearchWeb(max_results=5))
    registry.register(RealReadUrl(timeout=15))
    registry.register(FileWrite(workspace_root))
    registry.register(FileRead(workspace_root))
    registry.register(RunCode(workspace_root))
    registry.register(ListFiles(workspace_root))
    registry.register(LearningTodoWrite())
    return registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _session_manager, _llm_client, _tool_registry, _memory_store

    _session_manager = SessionManager()
    _memory_store = MemoryStore(base_dir="storage/memory")
    logger.info("Session manager + memory store initialized")

    try:
        _llm_client = _create_llm_client()
        logger.info("LLM client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")
        _llm_client = None

    _tool_registry = _create_tool_registry()
    logger.info("Tool registry initialized")

    yield

    _session_manager = None
    _llm_client = None
    _tool_registry = None
    _memory_store = None


def create_app() -> FastAPI:
    app = FastAPI(
        title="LearnAgent API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router)

    # ── WebSocket route ───────────────────────────────────────────────

    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        await websocket.accept()
        logger.info("ws connected  session=%s", session_id)

        session_mgr = get_session_manager()
        session = await session_mgr.get_session(session_id)
        if not session:
            session = await session_mgr.create_session()
            session_id = session.session_id

        await websocket.send_json({
            "type": "session_ready",
            "data": {
                "session_id": session_id,
                "topic": session.topic,
                "permission_mode": session.permission_mode,
            }
        })

        # Queue 解耦：agent 后台任务从这里读 permission 响应，
        # while 循环往这里写 —— 避免 agent_loop 占用 while 循环导致死锁
        perm_queue: asyncio.Queue = asyncio.Queue()
        agent_task: asyncio.Task | None = None

        # 提取/缓存 session 级别 topic 的工具集
        _cached_topic: str | None = None
        _cached_tools: ToolRegistry | None = None

        def _get_tools_for_topic(topic: str | None) -> ToolRegistry:
            """按主题创建 workspace 子目录，返回对应工具集。
            无 topic 时用 _default。"""
            nonlocal _cached_topic, _cached_tools
            effective = topic or "_default"
            if _cached_topic == effective and _cached_tools is not None:
                return _cached_tools

            # 防止路径穿越（topic 由 LLM/前端提供，不可信）
            if effective != "_default":
                if ".." in effective or "/" in effective or "\\" in effective:
                    effective = "_default"
                    logger.warning("topic 含非法字符，回退到 _default")

            base = os.path.realpath(
                os.path.join(os.path.dirname(__file__), "../../storage/workspace")
            )
            topic_root = os.path.realpath(os.path.join(base, effective))
            if not topic_root.startswith(base + os.sep):
                topic_root = os.path.join(base, "_default")
                logger.warning("topic 路径逃逸，回退到 _default")
            os.makedirs(topic_root, exist_ok=True)

            reg = ToolRegistry()
            reg.register(RealSearchWeb(max_results=5))
            reg.register(RealReadUrl(timeout=15))
            reg.register(FileWrite(topic_root))
            reg.register(FileRead(topic_root))
            reg.register(RunCode(topic_root))
            reg.register(ListFiles(topic_root))
            reg.register(LearningTodoWrite())
            _cached_topic = effective
            _cached_tools = reg
            logger.info("[ws] topic workspace: %s → %s", effective, topic_root)
            return reg

        async def run_agent(content: str):
            nonlocal session

            if session and not session.first_message:
                await session_mgr.update_session(
                    session_id, first_message=content, increment_count=True
                )
            elif session:
                await session_mgr.update_session(session_id, increment_count=True)

            await session_mgr.add_message(session_id, "user", content)

            if _llm_client is None:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "LLM 未配置，请设置 DEEPSEEK_API_KEY。"}
                })
                return

            async def on_event(event_type: str, event_data: dict):
                await websocket.send_json({"type": event_type, "data": event_data})

            async def ask_permission(tool_name: str, reason: str,
                                     tool_input: dict) -> bool:
                request_id = os.urandom(8).hex()
                await websocket.send_json({
                    "type": "permission_required",
                    "data": {
                        "request_id": request_id,
                        "tool_name": tool_name,
                        "reason": reason,
                        "tool_input": tool_input,
                    }
                })
                while True:
                    try:
                        resp = await asyncio.wait_for(perm_queue.get(), timeout=120.0)
                        if resp.get("request_id") == request_id:
                            return resp.get("approved", False)
                        await perm_queue.put(resp)
                    except asyncio.TimeoutError:
                        logger.warning("permission timeout  request=%s  tool=%s",
                                       request_id[:12], tool_name)
                        return False

            session = await session_mgr.get_session(session_id)
            history_messages = session.messages.copy() if session else []
            history_count = len(history_messages)
            messages = history_messages.copy()

            # ── LLM 路由：识别意图和主题（与 CLI 一致） ──
            intent = "chat"
            detected_topic: str | None = None
            if _llm_client is not None:
                try:
                    router = LLMRouter(_llm_client)
                    route = await router.route(content)
                    intent = route["intent"]
                    detected_topic = route.get("topic")
                    logger.info("[ws] route  intent=%s  topic=%s", intent, detected_topic)
                except Exception:
                    logger.debug("LLM 路由失败，回退到 chat", exc_info=True)

            # 更新 session topic
            effective_topic = detected_topic or (session.topic if session else None)
            if effective_topic and session:
                await session_mgr.update_session(session_id, topic=effective_topic)

            # ── Skill 注入（与 CLI 一致） ──
            skill_body: str | None = None
            skill_name = INTENT_TO_SKILL.get(intent)
            if skill_name:
                skills_dir = os.path.join(os.path.dirname(__file__), "../../skills")
                try:
                    from app.skills.loader import load_skill
                    skill = load_skill(skills_dir, skill_name)
                    if skill:
                        skill_body = skill.get("body")
                        logger.info("[ws] skill loaded  intent=%s  skill=%s", intent, skill_name)
                except Exception:
                    pass

            # ── 上下文压缩（与 CLI 同步） ──
            from app.context.compaction import estimate_tokens, compact_messages, BUDGET_WARNING
            tokens = estimate_tokens(messages)
            if tokens > BUDGET_WARNING:
                messages, removed = compact_messages(messages)
                if removed > 0:
                    logger.info("compacted  %d msgs removed  tokens=%d→%d",
                               removed, tokens, estimate_tokens(messages))

            system_prompt = build_system_prompt(
                current_topic=effective_topic,
                intent=intent,
                skill_body=skill_body,
                plan_mode=(session.permission_mode == "plan" if session else False),
            )
            logger.info("[ws] session=%s intent=%s topic=%s skill=%s history=%d prompt_len=%d",
                       session_id, intent, effective_topic,
                       skill_name or "none", history_count, len(system_prompt))

            try:
                result = await agent_loop(
                    messages=messages,
                    llm=_llm_client,
                    tools=_get_tools_for_topic(effective_topic),
                    system=system_prompt,
                    max_turns=8,
                    ask_callback=ask_permission,
                    on_event=on_event,
                    permission_mode=session.permission_mode if session else "default",
                )

                new_messages = result.get("messages", [])[history_count:]
                for msg in new_messages:
                    if msg.get("role") in ("user", "assistant"):
                        await session_mgr.add_message(
                            session_id, msg.get("role"), msg.get("content", "")
                        )

                # ── 长期记忆（与 CLI 一致） ──
                if _memory_store and intent in ("learn_concept", "analyze_repo", "review"):
                    if effective_topic:
                        last_content = ""
                        for m_text in reversed(result.get("messages", [])):
                            if m_text.get("role") == "assistant" and m_text.get("content"):
                                last_content = str(m_text["content"])[:500]
                                break
                        _memory_store.save(
                            name=f"topic_{effective_topic}",
                            memory_type="learning",
                            description=f"学习记录：{effective_topic}",
                            body=f"- 主题：{effective_topic}\n- 意图：{intent}\n- 最近摘要：{last_content}\n",
                        )
                        logger.info("[ws] memory saved  topic=%s", effective_topic)

                await websocket.send_json({
                    "type": "completed",
                    "data": {
                        "messages": new_messages,
                        "reason": result.get("reason", "completed"),
                    },
                })
            except Exception as e:
                logger.error("agent error: %s", e)
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": str(e)[:300]}
                })

        # ── 消息循环（不被 agent_loop 阻塞） ──
        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type")
                msg_data = data.get("data", {})

                if msg_type == "chat":
                    content = msg_data.get("content", "")
                    logger.info("[ws] user_input  session=%s  %s", session_id, content[:120])
                    if agent_task and not agent_task.done():
                        agent_task.cancel()
                    agent_task = asyncio.create_task(run_agent(content))

                elif msg_type == "permission_response":
                    await perm_queue.put(msg_data)

                elif msg_type == "set_mode":
                    mode = msg_data.get("mode", "default")
                    await session_mgr.update_session(session_id, permission_mode=mode)

        except Exception as e:
            logger.error("ws error: %s: %s", type(e).__name__, e)
        finally:
            if agent_task and not agent_task.done():
                agent_task.cancel()
            logger.info("ws closed  session=%s", session_id)

    # ── Mount static files ────────────────────────────────────────────

    static_dir = os.path.join(os.path.dirname(__file__), "../../web/dist")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), "static")

    return app
