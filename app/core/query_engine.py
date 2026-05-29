import os
import time
import uuid

from app.llm.base import LLMClient
from app.tools.registry import ToolRegistry
from app.core.agent_loop import agent_loop
from app.core.router import topic_distance, normalize_topic
from app.context.context_builder import build_system_prompt
from app.context.compaction import compact_messages, estimate_tokens, BUDGET_WARNING

INTENT_TO_SKILL = {
    "learn_concept": "learn-concept",
    "analyze_repo": "read-repo",
    "review": "review-progress",
}

SLASH_COMMANDS = {
    "/help": "显示可用命令",
    "/clear": "清空当前会话",
    "/plan": "进入/退出计划模式（只读探索→确认→执行）",
    "/topic": "查看或切换当前学习主题",
    "/progress": "查看学习任务进度",
    "/sessions": "列出历史会话",
    "/model": "显示当前模型信息",
    "/tools": "列出已注册工具",
    "/memory": "查看长期记忆",
    "/exit": "退出 LearnAgent",
}


class LearnQueryEngine:
    def __init__(
        self,
        llm: LLMClient,
        tools: ToolRegistry,
        session_store=None,
        memory_store=None,
        skills_dir: str | None = None,
    ):
        self.llm = llm
        self.tools = tools
        self.session_store = session_store
        self.memory_store = memory_store
        self.messages: list[dict] = []
        self.session_id = uuid.uuid4().hex[:12]
        self.current_topic: str | None = None
        self.permission_mode: str = "default"  # "default" | "plan"
        self.started_at = time.time()
        self._ask_callback = None
        self._on_event = None
        self._skills: dict[str, dict] = {}
        self._load_skills(skills_dir)

    def set_ask_callback(self, callback):
        self._ask_callback = callback

    def set_on_event(self, callback):
        self._on_event = callback

    def _load_skills(self, skills_dir: str | None):
        if not skills_dir or not os.path.isdir(skills_dir):
            return
        from app.skills.loader import list_skills
        for skill in list_skills(skills_dir):
            self._skills[skill["name"]] = skill

    def _get_skill_body(self, intent: str | None) -> str | None:
        if not intent:
            return None
        skill_name = INTENT_TO_SKILL.get(intent)
        if not skill_name:
            return None
        skill = self._skills.get(skill_name)
        return skill["body"] if skill else None

    def _update_topic(self, new_topic: str | None, intent: str | None) -> str | None:
        """根据 intent 和输入决定是否更新 topic。返回事件描述或 None。"""
        if not new_topic or intent == "chat":
            return None
        dist = topic_distance(self.current_topic, new_topic)
        if dist == "same":
            return None
        old = self.current_topic
        self.current_topic = new_topic
        if dist == "drift":
            return f"主题漂移：{old or '无'} → {new_topic}"
        return f"新主题：{new_topic}"

    async def submit_message(
        self,
        user_input: str,
        topic: str | None = None,
        intent: str | None = None,
    ) -> dict:
        if user_input.startswith("/"):
            return await self._handle_command(user_input)

        # topic 自动管理
        topic = normalize_topic(topic)
        topic_msg = self._update_topic(topic, intent)
        if topic_msg and self._on_event:
            await self._on_event("topic_change", {"message": topic_msg, "new_topic": self.current_topic})

        self.messages.append({"role": "user", "content": user_input})
        count_before = len(self.messages)

        skill_body = self._get_skill_body(intent)

        # 上下文压缩检查
        tokens = estimate_tokens(self.messages)
        if tokens > BUDGET_WARNING:
            self.messages, removed = compact_messages(self.messages)
            if removed > 0 and self._on_event:
                await self._on_event("compact", {"removed": removed, "tokens_before": tokens})

        system_prompt = build_system_prompt(
            current_topic=self.current_topic,
            intent=intent,
            skill_body=skill_body,
            plan_mode=(self.permission_mode == "plan"),
        )

        result = await agent_loop(
            messages=self.messages,
            llm=self.llm,
            tools=self.tools,
            system=system_prompt,
            max_turns=8,
            ask_callback=self._ask_callback if self._ask_callback else None,
            on_event=self._on_event if self._on_event else None,
            permission_mode=self.permission_mode,
        )

        if self.session_store:
            new_msgs = result["messages"][count_before:]
            for msg in new_msgs:
                self.session_store.append_message(self.session_id, msg)

        if self.memory_store and intent in ("learn_concept", "analyze_repo", "review"):
            self._save_topic_memory(topic, intent, result)

        if topic_msg:
            result["topic_change"] = topic_msg

        return result

    def _save_topic_memory(self, topic: str | None, intent: str, result: dict):
        if not topic:
            return
        last_content = ""
        for m in reversed(result.get("messages", [])):
            if m.get("role") == "assistant" and m.get("content"):
                last_content = str(m["content"])[:500]
                break
        body = f"- 主题：{topic}\n- 意图：{intent}\n- 最近摘要：{last_content}\n"
        self.memory_store.save(
            name=f"topic_{topic}",
            memory_type="learning",
            description=f"学习记录：{topic}",
            body=body,
        )

    async def _handle_command(self, command: str) -> dict:
        cmd = command.strip().split()[0]
        if cmd == "/help":
            lines = ["可用命令："]
            for name, desc in SLASH_COMMANDS.items():
                lines.append(f"  {name}  {desc}")
            return {"type": "command", "content": "\n".join(lines)}

        if cmd == "/clear":
            self.messages = []
            return {"type": "command", "content": "会话已清空。"}

        if cmd == "/topic":
            args = command.strip().split(maxsplit=1)
            if len(args) > 1:
                self.current_topic = normalize_topic(args[1])
                return {"type": "command", "content": f"学习主题已切换为：{self.current_topic}"}
            if self.current_topic:
                return {"type": "command", "content": f"当前学习主题：{self.current_topic}"}
            return {"type": "command", "content": "尚未设置学习主题。"}

        if cmd == "/progress":
            records = []
            if self.memory_store:
                records = self.memory_store.list_by_type("learning")
            if not records:
                return {"type": "command", "content": "暂无学习记录。"}
            lines = [f"学习进度（共 {len(records)} 条）："]
            for r in records[-10:]:
                lines.append(f"  - {r['description']}")
            if self.current_topic:
                lines.append(f"\n当前主题：{self.current_topic}")
            return {"type": "command", "content": "\n".join(lines)}

        if cmd == "/sessions":
            if not self.session_store:
                return {"type": "command", "content": "Session 存储未启用。"}
            base = self.session_store._base_dir
            if not os.path.isdir(base):
                return {"type": "command", "content": "暂无历史会话。"}
            files = [f for f in os.listdir(base) if f.endswith(".jsonl")]
            if not files:
                return {"type": "command", "content": "暂无历史会话。"}
            lines = [f"历史会话（共 {len(files)} 个）："]
            for f in sorted(files, reverse=True)[:10]:
                sid = f.replace(".jsonl", "")
                path = os.path.join(base, f)
                size = os.path.getsize(path)
                msgs = self.session_store.get_messages(sid)
                first = msgs[0]["content"][:40] if msgs else "(空)"
                marker = " ← 当前" if sid == self.session_id else ""
                lines.append(f"  {sid[:8]}  {len(msgs)}条 {size}字节 {first}{marker}")
            lines.append("\n恢复会话：python -m app.main --resume <id>")
            return {"type": "command", "content": "\n".join(lines)}

        if cmd == "/model":
            return {"type": "command", "content": f"当前模型：{self.llm.__class__.__name__}"}

        if cmd == "/tools":
            names = [t for t in self.tools._tools.keys()]
            return {"type": "command", "content": f"已注册工具：{', '.join(names)}"}

        if cmd == "/memory":
            if not self.memory_store:
                return {"type": "command", "content": "Memory 存储未启用。"}
            entries = self.memory_store.list_by_type("learning")
            if not entries:
                return {"type": "command", "content": "暂无学习记录。"}
            lines = ["学习记录："]
            for e in entries[-10:]:
                lines.append(f"  - {e['description']}")
            return {"type": "command", "content": "\n".join(lines)}

        if cmd == "/plan":
            if self.permission_mode == "plan":
                self.permission_mode = "default"
                return {"type": "command", "content": "已退出计划模式。现在可以执行写入和代码运行操作。"}
            self.permission_mode = "plan"
            return {"type": "command", "content": "已进入计划模式。只允许搜索、阅读等只读操作。确认计划后再次输入 /plan 退出。"}

        if cmd == "/exit":
            return {"type": "command", "content": "再见！"}

        return {"type": "command", "content": f"未知命令：{cmd}。输入 /help 查看可用命令。"}
