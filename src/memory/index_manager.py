import json
from pathlib import Path
from datetime import datetime
from src.memory.schemas import MemoryIndex, LearningEntry
from src.utils.path_safety import safe_write
from src.logging_config import setup_logging

logger = setup_logging()


class IndexManager:
    """管理 index.json（唯一 source of truth）+ 渲染 MEMORY.md。"""
    def __init__(self, base_dir: str = "data/memory"):
        self.base_dir = Path(base_dir)
        self.index_path = self.base_dir / "index.json"
        self.memory_md_path = self.base_dir / "MEMORY.md"

    def _ensure_dir(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> MemoryIndex:
        self._ensure_dir()
        if not self.index_path.exists():
            return MemoryIndex()
        data = json.loads(self.index_path.read_text(encoding="utf-8"))
        return MemoryIndex(**data)

    def save(self, index: MemoryIndex):
        self._ensure_dir()
        index.updated_at = datetime.utcnow()
        safe_write(self.index_path, index.model_dump_json(indent=2))
        self._render_memory_md(index)

    def add_learning(self, topic: str, path: str, tags: list[str] | None = None,
                     source: str = "react_agent", entry_id: str = ""):
        index = self.load()
        if not entry_id:
            ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            slug = topic.lower().replace(" ", "-")[:40]
            entry_id = f"learning-{ts}-{slug}"

        entry = LearningEntry(
            id=entry_id,
            topic=topic,
            path=path,
            source=source,
            tags=tags or [],
        )

        # 去重：同 topic 替换
        index.learnings = [e for e in index.learnings if e.topic != topic]
        index.learnings.append(entry)

        # 更新 recent_topics（去重，保持最近 10 条）
        if topic not in index.recent_topics:
            index.recent_topics.insert(0, topic)
        index.recent_topics = index.recent_topics[:10]

        self.save(index)
        logger.debug("index learning added", topic=topic)
        return entry

    def get_recent_learnings(self, limit: int = 5) -> list[LearningEntry]:
        index = self.load()
        sorted_learnings = sorted(index.learnings, key=lambda x: x.created_at, reverse=True)
        return sorted_learnings[:limit]

    def get_all_learnings(self) -> list[LearningEntry]:
        return self.load().learnings

    def _render_memory_md(self, index: MemoryIndex):
        lines = [
            "# LearnAgent Memory Index",
            "",
            "## User Profile",
            "用户画像保存在 `data/profile.json`",
            "",
            "## Learning Records",
            f"共 {len(index.learnings)} 条，保存在 `data/memory/learnings/`",
            "",
        ]
        if index.recent_topics:
            lines.append("### 最近主题")
            for t in index.recent_topics:
                lines.append(f"- {t}")
            lines.append("")

        recent = sorted(index.learnings, key=lambda x: x.created_at, reverse=True)[:20]
        if recent:
            lines.append("### 最近学习记录")
            lines.append("")
            for r in recent:
                date_str = r.created_at.strftime("%Y-%m-%d") if r.created_at else ""
                lines.append(f"- [{r.topic}]({r.path}) — {date_str}")
            lines.append("")

        lines.append("## Artifact Records")
        lines.append("产物保存在 `artifacts/`，索引在 `data/artifacts_index.jsonl`")
        lines.append("")

        self._ensure_dir()
        safe_write(self.memory_md_path, "\n".join(lines))
