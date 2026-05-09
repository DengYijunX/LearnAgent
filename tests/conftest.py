import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_llm_response():
    """返回 Mock LLM 的工厂函数"""
    def _make(text: str):
        mock = AsyncMock()
        mock.ainvoke.return_value = type("msg", (), {"content": text})()
        return mock
    return _make


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path
