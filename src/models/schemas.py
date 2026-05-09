from enum import Enum
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"


class InputType(str, Enum):
    KEYWORD = "keyword"
    GITHUB_URL = "github_url"
    DOC_URL = "doc_url"
    UNKNOWN = "unknown"


class UserInput(BaseModel):
    query: str = Field(..., description="用户输入的技术名称/链接/仓库地址")

    @property
    def input_type(self) -> InputType:
        q = self.query.strip()
        if q.startswith("https://github.com/"):
            return InputType.GITHUB_URL
        if q.startswith("http://") or q.startswith("https://"):
            return InputType.DOC_URL
        return InputType.KEYWORD


class RouterDecision(BaseModel):
    task_type: TaskType
    reason: str = ""


class KnowledgeSummary(BaseModel):
    topic: str
    core_concepts: list[str] = Field(default_factory=list)
    learning_points: list[str] = Field(default_factory=list)
    related_techs: list[str] = Field(default_factory=list)
