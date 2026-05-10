import json
from pathlib import Path
from datetime import datetime
from src.memory.schemas import UserProfileData
from src.utils.path_safety import safe_write
from src.logging_config import setup_logging

logger = setup_logging()


def load_profile(path: str = "data/profile.json") -> UserProfileData:
    """加载用户画像。兼容旧格式自动迁移。"""
    profile_path = Path(path)
    if not profile_path.exists():
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile = UserProfileData()
        save_profile(profile, path)
        logger.info("创建新用户画像", path=path)
        return profile

    data = json.loads(profile_path.read_text(encoding="utf-8"))
    # 兼容旧字段名
    if "version" not in data:
        data["version"] = "1.1"
        logger.info("用户画像自动迁移到 v1.1")
    return UserProfileData(**data)


def save_profile(profile: UserProfileData, path: str = "data/profile.json"):
    profile.updated_at = datetime.utcnow()
    profile_path = Path(path)
    safe_write(profile_path, profile.model_dump_json(indent=2))


def update_profile(profile: UserProfileData, topic: str):
    """追加 skills_learning + recent_topics（去重）。不自动加入 skills_known。"""
    if topic not in profile.skills_learning:
        profile.skills_learning.append(topic)
    if topic not in profile.recent_topics:
        profile.recent_topics.insert(0, topic)
    profile.recent_topics = profile.recent_topics[:10]


def mark_skill_known(profile: UserProfileData, topic: str):
    """将 topic 从 skills_learning 升级到 skills_known。"""
    if topic in profile.skills_learning:
        profile.skills_learning.remove(topic)
    if topic not in profile.skills_known:
        profile.skills_known.append(topic)


def profile_summary(profile: UserProfileData) -> str:
    """用户画像的人类可读摘要。"""
    parts = []
    if profile.skills_known:
        parts.append(f"已掌握: {', '.join(profile.skills_known)}")
    if profile.skills_learning:
        parts.append(f"学习中: {', '.join(profile.skills_learning)}")
    return " | ".join(parts) if parts else "新用户，开始你的学习之旅吧！"
