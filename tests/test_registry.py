from src.registry.registry import Registry, get_registry
from src.registry.permission import is_allowed
from src.registry.validator import validate_config


def test_registry_register_and_status():
    r = Registry()
    r.register("web_search", "Tools", provider="tavily", risk="low")
    r.register("content_fetch", "Tools", provider="jina+httpx")
    status = r.status()
    assert len(status) == 2
    names = [s["name"] for s in status]
    assert "web_search" in names
    assert "content_fetch" in names


def test_registry_status_text():
    r = Registry()
    r.register("web_search", "Tools", provider="tavily")
    text = r.status_text()
    assert "Tools" in text
    assert "web_search" in text


def test_registry_category_grouping():
    r = Registry()
    r.register("web_search", "Tools")
    r.register("slack", "Extensions")
    text = r.status_text()
    assert "Tools" in text
    assert "Extensions" in text


def test_is_allowed_default_true():
    assert is_allowed("web_search") is True


def test_get_registry_singleton():
    r1 = get_registry()
    r2 = get_registry()
    assert r1 is r2


def test_validate_config_warning_only():
    result = validate_config(strict=False)
    assert isinstance(result, bool)
