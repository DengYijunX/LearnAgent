"""Session 上下文 —— 用 ContextVar 安全传递 session_id，避免 os.environ 竞态。"""

from contextvars import ContextVar

current_session_id: ContextVar[str] = ContextVar("session_id", default="")
