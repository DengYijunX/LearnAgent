import os
import uuid

from app.llm.base import LLMClient
from app.tools.registry import ToolRegistry
from app.core.agent_loop import agent_loop
from app.context.context_builder import build_system_prompt

INTENT_TO_SKILL = {
    "learn_concept": "learn-concept",
    "analyze_repo": "read-repo",
    "review": "review-progress",
}

SLASH_COMMANDS = {
    "/help": "显示可用命令",
    "/clear": "清空当前会话",
    "/topic": "查看或切换当前学习主题",
    "/progress": "查看学习任务进度",
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
        self._ask_callback = None
        self._skills: dict[str, dict] = {}
        self._load_skills(skills_dir)

    def set_ask_callback(self, callback):
        self._ask_callback = callback

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

    async def submit_message(
        self,
        user_input: str,
        topic: str | None = None,
        intent: str | None = None,
    ) -> dict:
        if user_input.startswith("/"):
            return await self._handle_command(user_input)

        if topic:
            self.current_topic = topic

        self.messages.append({"role": "user", "content": user_input})
        count_before = len(self.messages)

        skill_body = self._get_skill_body(intent)

        system_prompt = build_system_prompt(
            current_topic=self.current_topic,
            intent=intent,
            skill_body=skill_body,
        )

        result = await agent_loop(
            messages=self.messages,
            llm=self.llm,
            tools=self.tools,
            system=system_prompt,
            max_turns=8,
            ask_callback=self._ask_callback if hasattr(self, "_ask_callback") else None,
        )

        if self.session_store:
            new_msgs = result["messages"][count_before:]
            for msg in new_msgs:
                self.session_store.append_message(self.session_id, msg)

        if self.memory_store and intent in ("learn_concept", "analyze_repo", "review"):
            self._save_topic_memory(topic, intent, result)

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
                self.current_topic = args[1]
                return {"type": "command", "content": f"当前学习主题已切换为：{args[1]}"}
            if self.current_topic:
                return {"type": "command", "content": f"当前学习主题：{self.current_topic}"}
            return {"type": "command", "content": "尚未设置学习主题。使用 /topic <主题名> 设置。"}

        if cmd == "/progress":
            records = []
            if self.memory_store:
                records = self.memory_store.list_by_type("learning")
            if not records:
                return {"type": "command", "content": "暂无学习记录。开始学习后会自动记录进度。"}
            lines = [f"学习进度（共 {len(records)} 条记录）："]
            for r in records[-10:]:
                lines.append(f"  - {r['description']}")
            if self.current_topic:
                lines.append(f"\n当前主题：{self.current_topic}")
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

        if cmd == "/exit":
            return {"type": "command", "content": "再见！"}

        return {"type": "command", "content": f"未知命令：{cmd}。输入 /help 查看可用命令。"}
