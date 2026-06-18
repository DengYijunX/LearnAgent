"""REST API routes for the LearnAgent web server."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from .session_manager import SessionManager


router = APIRouter(prefix="/api", tags=["api"])


# Request/Response Models
class ChatRequest(BaseModel):
    content: str
    session_id: Optional[str] = None
    intent: Optional[str] = None
    topic: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str


class SessionSummaryResponse(BaseModel):
    id: str
    message_count: int
    first_message: str
    topic: Optional[str]
    created_at: str
    updated_at: str


class SessionsResponse(BaseModel):
    sessions: List[SessionSummaryResponse]


class CreateSessionResponse(BaseModel):
    id: str
    created_at: str


class DeleteSessionResponse(BaseModel):
    deleted: bool


class ToolInfo(BaseModel):
    name: str
    description: str
    read_only: bool


class ToolsResponse(BaseModel):
    tools: List[ToolInfo]


class ConfigInfo(BaseModel):
    model_mode: str
    base_url: str
    storage_dir: str
    api_key_configured: bool


# Helper function to format session for response
def _format_session(session) -> Dict[str, Any]:
    return {
        "id": session.session_id,
        "message_count": session.message_count,
        "first_message": session.first_message,
        "topic": session.topic,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


@router.get("/sessions", response_model=SessionsResponse)
async def list_sessions():
    from .app import get_session_manager
    session_mgr = get_session_manager()
    sessions = await session_mgr.list_sessions()
    return {"sessions": [_format_session(s) for s in sessions]}


@router.post("/sessions", response_model=CreateSessionResponse, status_code=201)
async def create_session():
    from .app import get_session_manager
    session_mgr = get_session_manager()
    session = await session_mgr.create_session()
    return {
        "id": session.session_id,
        "created_at": session.created_at.isoformat(),
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    from .app import get_session_manager
    session_mgr = get_session_manager()
    session = await session_mgr.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        **_format_session(session),
        "permission_mode": session.permission_mode,
        "messages": session.messages,  # Return stored messages
    }


@router.delete("/sessions/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(session_id: str):
    from .app import get_session_manager
    session_mgr = get_session_manager()
    deleted = await session_mgr.delete_session(session_id)
    return {"deleted": deleted}


@router.post("/chat", response_model=ChatResponse, status_code=202)
async def send_chat(req: ChatRequest):
    """通过 HTTP 创建会话（实际对话走 WebSocket）。"""
    session_id = req.session_id
    if not session_id:
        from .app import get_session_manager
        session_mgr = get_session_manager()
        session = await session_mgr.create_session(topic=req.topic)
        session_id = session.session_id
    return {
        "session_id": session_id,
        "message": f"会话已就绪。连接到 ws://host/ws/{session_id} 开始对话。",
    }


@router.get("/tools", response_model=ToolsResponse)
async def list_tools():
    from .app import get_tool_registry
    registry = get_tool_registry()
    return {
        "tools": [
            {"name": name, "description": t.description, "read_only": t.is_read_only()}
            for name, t in registry._tools.items()
        ]
    }


@router.get("/config", response_model=ConfigInfo)
async def get_config():
    from app.config.settings import get_config as get_app_config
    cfg = get_app_config()
    return {
        "model_mode": cfg.model_mode,
        "base_url": cfg.base_url,
        "storage_dir": cfg.storage_base_dir,
        "api_key_configured": bool(cfg.api_key),
    }
