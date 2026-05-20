import pytest

from app.config.settings import Settings
from app.llm.model_selector import ModelSelector


@pytest.mark.parametrize("mode", ["normal", "summary", "lightweight"])
def test_model_selector_uses_small_model_for_light_modes(mode):
    settings = Settings(
        deepseek_small_model="deepseek-flash-id",
        deepseek_large_model="deepseek-pro-id",
    )

    selected = ModelSelector(settings).select_for_mode(mode)

    assert selected.model == "deepseek-flash-id"
    assert selected.size == "small"
    assert selected.mode == mode


@pytest.mark.parametrize("mode", ["deep", "planning", "repo_analysis"])
def test_model_selector_uses_large_model_for_heavy_modes(mode):
    settings = Settings(
        deepseek_small_model="deepseek-flash-id",
        deepseek_large_model="deepseek-pro-id",
    )

    selected = ModelSelector(settings).select_for_mode(mode)

    assert selected.model == "deepseek-pro-id"
    assert selected.size == "large"
    assert selected.mode == mode


@pytest.mark.parametrize(
    ("task", "expected"),
    [
        ("learn_concept", "deepseek-flash-id"),
        ("summarize_url", "deepseek-flash-id"),
        ("simple_chat", "deepseek-flash-id"),
        ("analyze_repo", "deepseek-pro-id"),
        ("plan_project", "deepseek-pro-id"),
        ("architecture_design", "deepseek-pro-id"),
    ],
)
def test_model_selector_maps_task_types(task, expected):
    settings = Settings(
        deepseek_small_model="deepseek-flash-id",
        deepseek_large_model="deepseek-pro-id",
    )

    selected = ModelSelector(settings).select_for_task(task)

    assert selected.model == expected


def test_model_selector_rejects_unknown_mode():
    selector = ModelSelector(Settings())

    with pytest.raises(ValueError, match="Unsupported model mode"):
        selector.select_for_mode("unknown")
