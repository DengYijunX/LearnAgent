"""Session manager for handling multiple concurrent learning sessions."""

import asyncio
import uuid
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from datetime import datetime


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
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, topic: Optional[str] = None) -> Session:
        async with self._lock:
            session_id = uuid.uuid4().hex[:12]
            session = Session(
                session_id=session_id,
                topic=topic,
            )
            self._sessions[session_id] = session
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
                return True
            return False
