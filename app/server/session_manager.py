"""Session manager for handling multiple concurrent learning sessions.

Sessions are persisted to disk via SessionStore so they survive server restarts.
"""

import asyncio
import uuid
import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Session:
    session_id: str
    topic: Optional[str] = None
    intent: str = "chat"
    created_at: datetime = None
    updated_at: datetime = None
    permission_mode: str = "default"
    message_count: int = 0
    first_message: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    todos: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


class SessionManager:
    def __init__(self, store=None):
        """store: app.memory.session_store.SessionStore（可选，传入则启用持久化）。"""
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self._store = store

    async def restore_from_disk(self) -> int:
        """从磁盘恢复所有会话。返回恢复的会话数量。"""
        if self._store is None:
            return 0
        async with self._lock:
            metas = self._store.list_session_metas()
            restored = 0
            for meta in metas:
                sid = meta["id"]
                # 从 JSONL 恢复消息
                try:
                    messages = self._store.get_messages(sid)
                except Exception:
                    messages = []
                session = Session(
                    session_id=sid,
                    topic=meta.get("topic"),
                    intent=meta.get("intent", "chat"),
                    created_at=datetime.fromisoformat(meta["created_at"])
                        if meta.get("created_at") else datetime.now(),
                    updated_at=datetime.fromisoformat(meta["updated_at"])
                        if meta.get("updated_at") else datetime.now(),
                    permission_mode=meta.get("permission_mode", "default"),
                    message_count=meta.get("message_count", len(messages)),
                    first_message=meta.get("first_message", ""),
                    messages=messages,
                    todos=meta.get("todos", []),
                )
                self._sessions[sid] = session
                restored += 1
            if restored:
                logger.info("restored %d sessions from disk", restored)
            return restored

    def _sync_meta(self, session: Session) -> None:
        """同步会话元数据到磁盘（同步方法，无锁）。"""
        if self._store is None:
            return
        try:
            self._store.save_session_meta(session.session_id, {
                "topic": session.topic,
                "intent": session.intent,
                "created_at": session.created_at.isoformat(),
                "permission_mode": session.permission_mode,
                "message_count": session.message_count,
                "first_message": session.first_message,
                "todos": session.todos,
            })
        except OSError as e:
            logger.warning("failed to sync session meta: %s", e)

    async def create_session(self, topic: Optional[str] = None) -> Session:
        async with self._lock:
            session_id = uuid.uuid4().hex[:12]
            session = Session(
                session_id=session_id,
                topic=topic,
            )
            self._sessions[session_id] = session
            self._sync_meta(session)
            return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        async with self._lock:
            return self._sessions.get(session_id)

    async def update_session(
        self,
        session_id: str,
        *,
        topic: Optional[str] = None,
        intent: Optional[str] = None,
        permission_mode: Optional[str] = None,
        first_message: Optional[str] = None,
        increment_count: bool = False,
    ) -> Optional[Session]:
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            if topic is not None:
                session.topic = topic
            if intent is not None:
                session.intent = intent
            if permission_mode is not None:
                session.permission_mode = permission_mode
            if first_message is not None:
                session.first_message = first_message
            if increment_count:
                session.message_count += 1
            session.updated_at = datetime.now()
            self._sync_meta(session)
            return session

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_call_id: Optional[str] = None,
    ) -> Optional[Session]:
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            message = {
                "role": role,
                "content": content,
            }
            if tool_call_id:
                message["tool_call_id"] = tool_call_id
            session.messages.append(message)
            session.updated_at = datetime.now()

            # 持久化消息到 JSONL
            if self._store:
                try:
                    self._store.append_message(session_id, message)
                except OSError as e:
                    logger.warning("failed to persist message: %s", e)
            return session

    async def update_todos(
        self,
        session_id: str,
        todos: List[Dict[str, Any]],
    ) -> Optional[Session]:
        """Replace a session's Todo snapshot without retaining caller references."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            session.todos = [dict(item) for item in todos]
            session.updated_at = datetime.now()
            self._sync_meta(session)
            return session

    async def list_sessions(self) -> list[Session]:
        async with self._lock:
            sessions = list(self._sessions.values())
            sessions.sort(key=lambda s: s.updated_at, reverse=True)
            return sessions

    async def delete_session(self, session_id: str) -> bool:
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                if self._store:
                    try:
                        self._store.delete_session(session_id)
                    except OSError as e:
                        logger.warning("failed to delete session from disk: %s", e)
                return True
            return False
