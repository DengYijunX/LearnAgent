import uuid

from app.llm.base import LLMClient
from app.tools.registry import ToolRegistry
from app.core.agent_loop import agent_loop
from app.context.context_builder import build_system_prompt

SLASH_COMMANDS = {
    "/help": "显示可用命令",
    "/clear": "清空当前会话",
    "/model": "显示当前模型信息",
    "/tools": "列出已注册工具",
    "/exit": "退出 LearnAgent",
}


class LearnQueryEngine:
    def __init__(self, llm: LLMClient, tools: ToolRegistry):
        self.llm = llm
        self.tools = tools
        self.messages: list[dict] = []
        self.session_id = uuid.uuid4().hex[:12]

    async def submit_message(
        self,
        user_input: str,
        topic: str | None = None,
        intent: str | None = None,
    ) -> dict:
        if user_input.startswith("/"):
            return await self._handle_command(user_input)

        self.messages.append({"role": "user", "content": user_input})

        system_prompt = build_system_prompt(
            current_topic=topic,
            intent=intent,
        )

        result = await agent_loop(
            messages=self.messages,
            llm=self.llm,
            tools=self.tools,
            system=system_prompt,
            max_turns=8,
        )

        return result

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

        if cmd == "/model":
            return {"type": "command", "content": f"当前模型：{self.llm.__class__.__name__}"}

        if cmd == "/tools":
            names = [t for t in self.tools._tools.keys()]
            return {"type": "command", "content": f"已注册工具：{', '.join(names)}"}

        if cmd == "/exit":
            return {"type": "command", "content": "再见！"}

        return {"type": "command", "content": f"未知命令：{cmd}。输入 /help 查看可用命令。"}
