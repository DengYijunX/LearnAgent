"""Skill 加载器 —— 读取 SKILL.md 并解析 YAML frontmatter。"""

import os
import yaml


def load_skill(skill_dir: str) -> dict | None:
    """加载单个 skill 目录下的 SKILL.md 文件。"""
    path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        meta = yaml.safe_load(parts[1].strip())
    except yaml.YAMLError:
        return None
    if not isinstance(meta, dict):
        return None
    return {
        "name": meta.get("name", ""),
        "description": meta.get("description", ""),
        "when_to_use": meta.get("when_to_use", ""),
        "allowed_tools": meta.get("allowed-tools", []),
        "argument_hint": meta.get("argument-hint", ""),
        "body": parts[2].strip(),
    }


def list_skills(skills_dir: str) -> list[dict]:
    """列出 skills 目录下所有可用 skill。"""
    results = []
    if not os.path.isdir(skills_dir):
        return results
    for entry in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, entry)
        if os.path.isdir(skill_path):
            skill = load_skill(skill_path)
            if skill:
                results.append(skill)
    return results
