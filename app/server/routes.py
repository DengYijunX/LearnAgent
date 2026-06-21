"""REST API routes for the LearnAgent web server."""

from fastapi import APIRouter, HTTPException, Query
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


def _format_todo(todo: Dict[str, Any]) -> Dict[str, Any]:
    """Return the stable Web Todo shape for CLI and Web-style inputs."""
    status = todo.get("status", "pending")
    if status not in {"pending", "in_progress", "completed"}:
        status = "pending"
    return {
        "content": str(todo.get("content", "")).strip(),
        "active_form": todo.get("active_form", todo.get("activeForm")),
        "status": status,
    }


def _bounded_memory(item: Dict[str, Any], body_limit: int = 500) -> Dict[str, str]:
    """Expose only the non-sensitive memory fields with a bounded body."""
    return {
        "name": str(item.get("name", "")),
        "description": str(item.get("description", "")),
        "type": str(item.get("type", "")),
        "body": str(item.get("body", ""))[:body_limit],
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
        "intent": session.intent,
        "permission_mode": session.permission_mode,
        "messages": session.messages,
    }


@router.get("/sessions/{session_id}/todos")
async def get_session_todos(session_id: str):
    from .app import get_session_manager
    session = await get_session_manager().get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"todos": [_format_todo(todo) for todo in session.todos]}


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


@router.get("/memories")
async def list_memories(
    memory_type: str = Query("learning", alias="type"),
    limit: int = Query(10, ge=1, le=50),
):
    from .app import get_memory_store
    entries = get_memory_store().list_by_type(memory_type)
    bounded = [_bounded_memory(entry) for entry in entries[-limit:]]
    return {"memories": bounded}


# ── 后台进程管理 ──

@router.get("/processes")
async def list_processes(session_id: str = ""):
    from app.process_manager import get_process_manager
    pm = get_process_manager()
    if pm is None:
        return {"processes": []}
    return {"processes": pm.list_all(session_id=session_id)}


@router.post("/processes/{pid}/stop")
async def stop_process(pid: int, session_id: str = ""):
    from app.process_manager import get_process_manager
    pm = get_process_manager()
    if pm is None:
        raise HTTPException(status_code=503, detail="Process manager not available")
    ok = await pm.stop(pid, session_id=session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Process not found or already stopped")
    return {"stopped": True, "pid": pid}
