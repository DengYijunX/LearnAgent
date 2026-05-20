"""Rule-based model selection for the first implementation stage."""

from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import Settings


SMALL_MODEL_MODES = {"normal", "summary", "lightweight"}
LARGE_MODEL_MODES = {"deep", "planning", "repo_analysis"}

TASK_MODE_MAP = {
    "learn_concept": "normal",
    "summarize_url": "summary",
    "read_document": "summary",
    "generate_learning_path": "normal",
    "analyze_repo": "repo_analysis",
    "plan_project": "planning",
    "architecture_design": "planning",
    "simple_chat": "normal",
}


@dataclass(frozen=True)
class ModelSelection:
    model: str
    size: str
    mode: str


class ModelSelector:
    def __init__(self, settings: Settings):
        self._settings = settings

    def select_for_mode(self, mode: str | None = None) -> ModelSelection:
        selected_mode = mode or self._settings.model_mode
        if selected_mode in SMALL_MODEL_MODES:
            return ModelSelection(
                model=self._settings.deepseek_small_model,
                size="small",
                mode=selected_mode,
            )
        if selected_mode in LARGE_MODEL_MODES:
            return ModelSelection(
                model=self._settings.deepseek_large_model,
                size="large",
                mode=selected_mode,
            )
        raise ValueError(f"Unsupported model mode: {selected_mode}")

    def select_for_task(self, task_type: str) -> ModelSelection:
        mode = TASK_MODE_MAP.get(task_type, self._settings.model_mode)
        return self.select_for_mode(mode)
