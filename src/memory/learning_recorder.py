import yaml
from pathlib import Path
from datetime import datetime
from src.models.schemas import KnowledgeSummary
from src.memory.index_manager import IndexManager
from src.memory.schemas import Frontmatter
from src.utils.path_safety import safe_write
from src.logging_config import setup_logging

logger = setup_logging()


class LearningRecorder:
    """负责写入 learnings/*.md 和更新 index.json。"""
    def __init__(self, index_manager: IndexManager, learnings_dir: str = "data/memory/learnings"):
        self.index_manager = index_manager
        self.learnings_dir = Path(learnings_dir)
        self.learnings_dir.mkdir(parents=True, exist_ok=True)

    def save_learning(self, topic: str, summary: KnowledgeSummary,
                      source: str = "react_agent", related_topics: list[str] | None = None,
                      artifact_path: str = "") -> Frontmatter:
        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")
        slug = topic.lower().replace(" ", "-")[:50]
        filename = f"{date_str}-{slug}.md"
        path = self.learnings_dir / filename

        tags = [t.lower().replace(" ", "-") for t in summary.core_concepts[:5]]
        for rt in summary.related_techs[:5]:
            tags.append(rt.lower().replace(" ", "-"))
        tags = list(dict.fromkeys(tags))[:8]

        entry_id = f"learning-{now.strftime('%Y%m%d-%H%M%S')}-{slug[:30]}"

        fm = Frontmatter(
            id=entry_id,
            topic=topic,
            source=source,
            created_at=now,
            related_topics=related_topics or summary.related_techs[:5],
            tags=tags,
            artifact_path=artifact_path,
        )

        # markdown 正文
        body_parts = [
            f"# {topic} 学习记录",
            "",
            "## 用户问题",
            f"{topic}",
            "",
            "## 核心概念",
        ]
        for c in summary.core_concepts:
            body_parts.append(f"- {c}")
        body_parts.append("")
        body_parts.append("## 学习要点")
        for i, p in enumerate(summary.learning_points, 1):
            body_parts.append(f"{i}. {p}")
        body_parts.append("")
        if summary.related_techs:
            body_parts.append("## 相关技术")
            for t in summary.related_techs:
                body_parts.append(f"- {t}")
            body_parts.append("")

        # YAML frontmatter + markdown
        yaml_str = yaml.dump(fm.model_dump(mode="json"), allow_unicode=True, sort_keys=False)
        content = f"---\n{yaml_str}---\n\n" + "\n".join(body_parts)
        safe_write(path, content)

        # 更新 index
        relative_path = str(path)
        self.index_manager.add_learning(
            topic=topic,
            path=relative_path,
            tags=tags,
            source=source,
            entry_id=entry_id,
        )

        logger.info("learning saved", topic=topic, path=relative_path)
        return fm

    def search_memory(self, query: str, limit: int = 5) -> list[dict]:
        """基于 index.json 的关键词匹配。只返回 metadata，不读完整 md。"""
        index = self.index_manager.load()
        results = []
        query_lower = query.lower()
        for entry in index.learnings:
            score = 0
            if query_lower in entry.topic.lower():
                score += 3
            for tag in entry.tags:
                if query_lower in tag.lower():
                    score += 1
            if score > 0:
                results.append({
                    "topic": entry.topic,
                    "path": entry.path,
                    "type": entry.type.value if entry.type else "learning_record",
                    "tags": entry.tags,
                    "created_at": entry.created_at.isoformat() if entry.created_at else "",
                    "score": score,
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def get_recent_learnings(self, limit: int = 5) -> list[dict]:
        entries = self.index_manager.get_recent_learnings(limit)
        return [
            {
                "topic": e.topic,
                "path": e.path,
                "tags": e.tags,
                "created_at": e.created_at.isoformat() if e.created_at else "",
            }
            for e in entries
        ]
