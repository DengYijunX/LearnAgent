from src.memory.index_manager import IndexManager
from src.memory.learning_recorder import LearningRecorder
from src.memory.user_profile import load_profile, save_profile, update_profile, profile_summary
from src.memory.session_logger import SessionLogger
from src.tools.artifact_writer import write_summary
from src.models.schemas import KnowledgeSummary
from src.logging_config import setup_logging

logger = setup_logging()


class MemoryManager:
    """统一的记忆层入口。Agent 只通过这个类访问记忆功能。"""

    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.index_mgr = IndexManager(f"{base_dir}/memory")
        self.recorder = LearningRecorder(self.index_mgr, f"{base_dir}/memory/learnings")
        self.profile = load_profile(f"{base_dir}/profile.json")
        self.session = SessionLogger(f"{base_dir}/sessions")

    def save_learning(self, topic: str, summary: KnowledgeSummary,
                      source: str = "react_agent"):
        """保存学习记录 + 更新画像 + 写产物。失败不抛异常。"""
        try:
            self.recorder.save_learning(topic, summary, source=source)
        except Exception as e:
            logger.warning("save_learning failed", topic=topic, error=str(e))

    def update_profile(self, topic: str):
        """更新用户画像（追加 skills_learning + recent_topics）。"""
        try:
            update_profile(self.profile, topic)
            save_profile(self.profile, f"{self.base_dir}/profile.json")
        except Exception as e:
            logger.warning("update_profile failed", topic=topic, error=str(e))

    def write_artifact(self, topic: str, summary: KnowledgeSummary):
        """写入学习产物到 artifacts/。"""
        try:
            write_summary(topic, summary)
        except Exception as e:
            logger.warning("write_artifact failed", topic=topic, error=str(e))

    def search_memory(self, query: str, limit: int = 5) -> list[dict]:
        """搜索记忆（关键词匹配 index.json）。"""
        return self.recorder.search_memory(query, limit)

    def get_recent(self, limit: int = 5) -> list[dict]:
        """获取最近学习记录。"""
        return self.recorder.get_recent_learnings(limit)

    def get_profile_summary(self) -> str:
        """获取用户画像摘要。"""
        return profile_summary(self.profile)

    def log(self, event_type: str, data: dict | None = None):
        """记录会话事件。"""
        try:
            self.session.log(event_type, data or {})
        except Exception:
            pass

    def log_plan_execute_complete(self, project_dir: str, generated_files: list,
                                  step_count: int):
        self.session.log_plan_execute_complete(project_dir, generated_files, step_count)
