LARGE_MODEL_MODES = {"deep", "planning", "repo_analysis"}

INTENT_TO_MODE = {
    "analyze_repo": "repo_analysis",
    "plan_project": "planning",
    "architecture_design": "planning",
}


class ModelSelector:
    def __init__(self, small_model: str, large_model: str):
        self.small_model = small_model
        self.large_model = large_model

    def select(self, mode: str) -> str:
        if mode in LARGE_MODEL_MODES:
            return self.large_model
        return self.small_model

    def select_for_intent(self, intent: str) -> str:
        mode = INTENT_TO_MODE.get(intent, "normal")
        return self.select(mode)
