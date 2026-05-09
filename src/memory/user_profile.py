import json
import os
from pydantic import BaseModel
from src.logging_config import setup_logging

logger = setup_logging()


class UserProfile(BaseModel):
    skills_known: list[str] = []
    skills_learning: list[str] = []
    preferred_difficulty: str = "beginner"
    preferred_language: str = "python"
    learning_goals: list[str] = []


def load_profile(path: str = "data/profile.json") -> UserProfile:
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        profile = UserProfile()
        save_profile(profile, path)
        logger.info("创建新用户画像", path=path)
        return profile
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return UserProfile(**data)


def save_profile(profile: UserProfile, path: str = "data/profile.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(), f, ensure_ascii=False, indent=2)
    logger.debug("用户画像已保存", path=path)
