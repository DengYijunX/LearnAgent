import os
from src.logging_config import setup_logging

logger = setup_logging()


def create_project(base_dir: str, project_name: str) -> str:
    """在 base_dir 下创建项目目录，含 README.md"""
    project_path = os.path.join(base_dir, project_name)
    os.makedirs(project_path, exist_ok=True)
    readme = os.path.join(project_path, "README.md")
    with open(readme, "w", encoding="utf-8") as f:
        f.write(f"# {project_name}\n\nLearnAgent 教学项目\n")
    logger.info("create_project", path=project_path)
    return project_path


def write_file(project_path: str, filename: str, content: str) -> str:
    """在项目目录下写文件"""
    file_path = os.path.join(project_path, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("write_file", path=file_path, size=len(content))
    return file_path
