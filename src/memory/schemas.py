from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    USER_PROFILE = "user_profile"
    LEARNING_RECORD = "learning_record"
    SESSION_LOG = "session_log"
    BOOKMARK = "bookmark"


class LearningStatus(str, Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"


class Frontmatter(BaseModel):
    id: str
    topic: str
    type: MemoryType = MemoryType.LEARNING_RECORD
    source: str = "react_agent"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    difficulty: str = "beginner"
    status: LearningStatus = LearningStatus.COMPLETED
    related_topics: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    artifact_path: str = ""


class LearningEntry(BaseModel):
    id: str
    topic: str
    path: str
    type: MemoryType = MemoryType.LEARNING_RECORD
    source: str = "react_agent"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tags: list[str] = Field(default_factory=list)


class MemoryIndex(BaseModel):
    version: str = "1.1"
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    learnings: list[LearningEntry] = Field(default_factory=list)
    recent_topics: list[str] = Field(default_factory=list)


class UserProfileData(BaseModel):
    version: str = "1.1"
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    skills_known: list[str] = Field(default_factory=list)
    skills_learning: list[str] = Field(default_factory=list)
    preferred_difficulty: str = "beginner"
    preferred_language: str = "python"
    learning_goals: list[str] = Field(default_factory=list)
    recent_topics: list[str] = Field(default_factory=list)
    weak_points: list[str] = Field(default_factory=list)
    completed_projects: list[str] = Field(default_factory=list)
    preferred_learning_style: str = "project_based"


class SessionEvent(BaseModel):
    time: datetime = Field(default_factory=datetime.utcnow)
    type: str
    query: str | None = None
    task_type: str | None = None
    step_count: int | None = None
    path: str | None = None
    generated_files: list[str] | None = None
    project_dir: str | None = None
    metadata: dict = Field(default_factory=dict)


class ArtifactRecord(BaseModel):
    artifact_id: str
    type: str
    topic: str
    path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
