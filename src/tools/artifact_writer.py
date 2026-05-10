import json
from pathlib import Path
from datetime import datetime
from src.utils.path_safety import safe_path, safe_write
from src.models.schemas import KnowledgeSummary
from src.logging_config import setup_logging

logger = setup_logging()

_ARTIFACTS_DIR = Path("artifacts")
_INDEX_PATH = Path("data/artifacts_index.jsonl")


def _ensure_dirs():
    for sub in ["summaries", "projects", "learning_paths"]:
        (_ARTIFACTS_DIR / sub).mkdir(parents=True, exist_ok=True)
    _INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)


def _append_index(record: dict):
    _ensure_dirs()
    with open(_INDEX_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_summary(topic: str, summary: KnowledgeSummary) -> str:
    """输出学习总结到 artifacts/summaries/<date>-<topic>-summary.md。"""
    _ensure_dirs()
    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    slug = topic.lower().replace(" ", "-")[:40]
    filename = f"{date_str}-{slug}-summary.md"
    path = safe_path(str(_ARTIFACTS_DIR / "summaries"), filename)

    artifact_id = f"artifact-{now.strftime('%Y%m%d-%H%M%S')}-{slug[:20]}"

    lines = [
        f"# {topic} — 学习总结",
        "",
        f"**日期**: {date_str}",
        "",
        "## 核心概念",
    ]
    for c in summary.core_concepts:
        lines.append(f"- {c}")
    lines.append("")
    lines.append("## 学习要点")
    for i, p in enumerate(summary.learning_points, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    if summary.related_techs:
        lines.append("## 相关技术")
        for t in summary.related_techs:
            lines.append(f"- {t}")
        lines.append("")

    safe_write(path, "\n".join(lines))

    _append_index({
        "artifact_id": artifact_id,
        "type": "summary",
        "topic": topic,
        "path": str(path),
        "created_at": now.isoformat(),
    })

    logger.info("artifact written", type="summary", topic=topic, path=str(path))
    return str(path)


def write_project_doc(topic: str, content: str) -> str:
    """输出项目产物到 artifacts/projects/<date>-<topic>-project.md。"""
    _ensure_dirs()
    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    slug = topic.lower().replace(" ", "-")[:40]
    filename = f"{date_str}-{slug}-project.md"
    path = safe_path(str(_ARTIFACTS_DIR / "projects"), filename)

    artifact_id = f"artifact-{now.strftime('%Y%m%d-%H%M%S')}-{slug[:20]}"

    lines = [
        f"# {topic} — 项目学习产物",
        "",
        f"**日期**: {date_str}",
        "",
        content,
    ]

    safe_write(path, "\n".join(lines))

    _append_index({
        "artifact_id": artifact_id,
        "type": "project",
        "topic": topic,
        "path": str(path),
        "created_at": now.isoformat(),
    })

    logger.info("artifact written", type="project", topic=topic, path=str(path))
    return str(path)
