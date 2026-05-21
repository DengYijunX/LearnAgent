"""Stage-one LearnAgent workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.agent_loop import run_agent_loop
from app.core.output_schema import LearningOutput
from app.core.router import InputRouter
from app.llm.base import LLMClient
from app.memory.memory_store import MemoryEntry, MemoryStore
from app.memory.session_store import SessionStore
from app.tools.registry import ToolRegistry


@dataclass(frozen=True)
class WorkflowResult:
    intent: str
    topic: str
    content: str
    output: LearningOutput
    session_id: str
    metadata: dict[str, Any]


class LearnWorkflow:
    def __init__(
        self,
        llm: LLMClient,
        tools: ToolRegistry,
        session_store: SessionStore,
        memory_store: MemoryStore,
        session_id: str | None = None,
        router: InputRouter | None = None,
        model_mode: str | None = None,
    ):
        self.llm = llm
        self.tools = tools
        self.session_store = session_store
        self.memory_store = memory_store
        self.session_id = session_id or f"session-{uuid4().hex[:12]}"
        self.router = router or InputRouter()
        self.model_mode = model_mode

    async def run(self, user_input: str) -> WorkflowResult:
        route = self.router.route(user_input)
        self.session_store.append_event(
            self.session_id,
            {"type": "user_input", "content": user_input},
        )
        self.session_store.append_event(
            self.session_id,
            {
                "type": "route",
                "intent": route.intent,
                "topic": route.topic,
                "suggested_tools": route.suggested_tools,
            },
        )

        loop_result = await run_agent_loop(
            llm=self.llm,
            tools=self.tools,
            messages=[{"role": "user", "content": user_input}],
            system_prompt=_build_system_prompt(route.intent),
            mode=self.model_mode or _mode_for_intent(route.intent),
            tool_context={
                "session_id": self.session_id,
                "current_topic": route.topic,
                "intent": route.intent,
            },
        )
        result = WorkflowResult(
            intent=route.intent,
            topic=route.topic,
            content=loop_result.final_content,
            output=LearningOutput.from_text(loop_result.final_content),
            session_id=self.session_id,
            metadata={"reason": loop_result.reason, "turns": loop_result.turns},
        )

        self.session_store.append_event(
            self.session_id,
            {
                "type": "assistant_output",
                "intent": result.intent,
                "topic": result.topic,
                "content": result.content,
                "output": result.output.to_dict(),
                "metadata": result.metadata,
            },
        )
        self.memory_store.save(
            MemoryEntry(
                name=f"{self.session_id}_{route.topic}",
                description=f"{route.topic} 学习结果",
                type="learning",
                body=result.content,
            )
        )
        return result


def create_default_storage(root: Path | str = "storage") -> tuple[SessionStore, MemoryStore]:
    storage_root = Path(root)
    return (
        SessionStore(storage_root / "sessions"),
        MemoryStore(storage_root / "memory"),
    )


def _build_system_prompt(intent: str) -> str:
    return (
        "你是 LearnAgent，一个面向自学者的 AI 学习助手。"
        "请围绕用户目标给出清晰、可执行、适合第一阶段的学习帮助。"
        "输出应覆盖 summary、concepts、learning_path、practice_tasks、related_topics、sources 这些信息。"
        f"当前意图：{intent}。"
    )


def _mode_for_intent(intent: str) -> str:
    if intent in {"analyze_repo", "plan_project", "architecture_design"}:
        return "repo_analysis"
    return "normal"
