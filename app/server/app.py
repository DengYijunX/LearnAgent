"""FastAPI application factory for LearnAgent web server."""

import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 配置日志
logging.basicConfig(level=logging.INFO)
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
from app.llm.deepseek_client import DeepSeekLLMClient
from app.tools.registry import ToolRegistry
from app.tools.search_web import MockSearchWeb
from app.tools.read_url import MockReadUrl
from app.tools.workspace_tools import FileWrite, FileRead, RunCode, ListFiles
from app.tools.todo_tools import LearningTodoWrite
from app.core.agent_loop import agent_loop


# 全局变量
_session_manager: Optional[SessionManager] = None
_llm_client: Optional[DeepSeekLLMClient] = None
_tool_registry: Optional[ToolRegistry] = None


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
    workspace_root = os.path.join(os.path.dirname(__file__), "../../storage/workspace")
    
    registry = ToolRegistry()
    registry.register(MockSearchWeb())
    registry.register(MockReadUrl())
    registry.register(FileWrite(workspace_root))
    registry.register(FileRead(workspace_root))
    registry.register(RunCode(workspace_root))
    registry.register(ListFiles(workspace_root))
    registry.register(LearningTodoWrite())
    return registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _session_manager, _llm_client, _tool_registry

    _session_manager = SessionManager()
    logger.info("Session manager initialized")

    try:
        _llm_client = _create_llm_client()
        logger.info("LLM client initialized successfully")
        logger.info(f"API Key: {os.getenv('DEEPSEEK_API_KEY', 'Not set')[:10]}...")
        logger.info(f"Model: {os.getenv('DEEPSEEK_SMALL_MODEL', 'Not set')}")
    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")
        _llm_client = None

    _tool_registry = _create_tool_registry()
    logger.info("Tool registry initialized")

    yield

    _session_manager = None
    _llm_client = None
    _tool_registry = None


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

    # WebSocket route
    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        await websocket.accept()
        print(f"WebSocket accepted for session: {session_id}")

        session_mgr = get_session_manager()
        session = await session_mgr.get_session(session_id)
        if not session:
            session = await session_mgr.create_session()
            session_id = session.session_id

        # 发送 session_ready 事件
        await websocket.send_json({
            "type": "session_ready",
            "data": {
                "session_id": session_id,
                "topic": session.topic,
                "permission_mode": session.permission_mode,
            }
        })
        print(f"Sent session_ready event")

        # 权限处理相关
        pending_permissions: Dict[str, asyncio.Event] = {}
        permission_results: Dict[str, bool] = {}

        # 接收消息
        try:
            while True:
                data = await websocket.receive_json()
                print(f"Received message: {data}")

                msg_type = data.get("type")
                msg_data = data.get("data", {})

                if msg_type == "chat":
                    content = msg_data.get("content", "")
                    print(f"Received chat message: {content}")

                    # 更新会话
                    if session and not session.first_message:
                        await session_mgr.update_session(
                            session_id, first_message=content, increment_count=True
                        )
                    elif session:
                        await session_mgr.update_session(session_id, increment_count=True)

                    # 添加用户消息到会话历史
                    await session_mgr.add_message(session_id, "user", content)

                    # 检查 LLM 客户端
                    if _llm_client is None:
                        await websocket.send_json({
                            "type": "error",
                            "data": {
                                "message": "LLM client is not configured. Please set DEEPSEEK_API_KEY environment variable."
                            }
                        })
                        continue

                    # 事件回调
                    async def on_event(event_type: str, event_data: dict):
                        await websocket.send_json({
                            "type": event_type,
                            "data": event_data
                        })

                    # 权限询问回调
                    async def ask_permission(tool_name: str, reason: str, tool_input: dict) -> bool:
                        request_id = os.urandom(8).hex()
                        event = asyncio.Event()
                        pending_permissions[request_id] = event

                        await websocket.send_json({
                            "type": "permission_required",
                            "data": {
                                "request_id": request_id,
                                "tool_name": tool_name,
                                "reason": reason,
                                "tool_input": tool_input,
                            }
                        })

                        try:
                            await asyncio.wait_for(event.wait(), timeout=120.0)
                        except asyncio.TimeoutError:
                            return False

                        return permission_results.pop(request_id, False)

                    # 获取会话历史消息（用于维护上下文）
                    session = await session_mgr.get_session(session_id)
                    history_messages = session.messages if session else []
                    history_count = len(history_messages)  # 记录历史消息数量

                    # 构建发送给 Agent 的消息列表（包含历史上下文）
                    messages = history_messages.copy()

                    try:
                        result = await agent_loop(
                            messages=messages,
                            llm=_llm_client,
                            tools=_tool_registry,
                            max_turns=8,
                            ask_callback=ask_permission,
                            on_event=on_event,
                            permission_mode=session.permission_mode if session else "default",
                        )

                        # 只返回新消息（不包括历史消息）
                        new_messages = result.get("messages", [])[history_count:]

                        # 将新消息添加到会话历史
                        for msg in new_messages:
                            if msg.get("role") in ["user", "assistant"]:
                                await session_mgr.add_message(
                                    session_id,
                                    msg.get("role"),
                                    msg.get("content", "")
                                )

                        await websocket.send_json({
                            "type": "completed",
                            "data": {
                                "messages": new_messages,  # 只返回新消息
                                "reason": result.get("reason", "completed"),
                                "summary": {
                                    "turns": len([m for m in new_messages if m.get("role") == "assistant"]),
                                    "tools": {},
                                },
                            },
                        })
                    except Exception as e:
                        print(f"Agent error: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": f"Agent error: {str(e)}"}
                        })

                elif msg_type == "permission_response":
                    req_id = msg_data.get("request_id")
                    approved = msg_data.get("approved", False)
                    permission_results[req_id] = approved
                    if req_id in pending_permissions:
                        pending_permissions[req_id].set()

                elif msg_type == "set_mode":
                    mode = msg_data.get("mode", "default")
                    await session_mgr.update_session(session_id, permission_mode=mode)

        except Exception as e:
            print(f"WebSocket error: {type(e).__name__}: {e}")
        finally:
            print(f"WebSocket closed for session: {session_id}")

    # Mount static files
    static_dir = os.path.join(os.path.dirname(__file__), "../../web/dist")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), "static")

    return app
