"""Tests for concrete tool implementations."""

import pytest


class TestSearchWeb:
    @pytest.mark.asyncio
    async def test_mock_returns_query_in_result(self):
        from app.tools.search_web import MockSearchWeb

        tool = MockSearchWeb()
        result = await tool.call({"query": "LangGraph"})
        assert "LangGraph" in str(result)

    @pytest.mark.asyncio
    async def test_mock_is_read_only(self):
        from app.tools.search_web import MockSearchWeb

        assert MockSearchWeb().is_read_only() is True

    def test_input_schema_has_query(self):
        from app.tools.search_web import MockSearchWeb

        schema = MockSearchWeb().input_schema
        assert "query" in schema.get("properties", {})


class TestReadUrl:
    @pytest.mark.asyncio
    async def test_mock_returns_url_in_result(self):
        from app.tools.read_url import MockReadUrl

        tool = MockReadUrl()
        result = await tool.call({"url": "https://example.com"})
        assert "https://example.com" in str(result)

    @pytest.mark.asyncio
    async def test_mock_is_read_only(self):
        from app.tools.read_url import MockReadUrl

        assert MockReadUrl().is_read_only() is True


class TestLearningTodoWrite:
    @pytest.mark.asyncio
    async def test_mock_saves_todos(self):
        from app.tools.todo_tools import LearningTodoWrite

        tool = LearningTodoWrite()
        result = await tool.call({
            "todos": [
                {"content": "理解 Agent Loop", "status": "in_progress"},
                {"content": "学习 LangGraph", "status": "pending"},
            ]
        })
        assert result.get("saved") is True
        assert result.get("count") == 2

    @pytest.mark.asyncio
    async def test_todo_write_is_not_read_only(self):
        from app.tools.todo_tools import LearningTodoWrite

        assert LearningTodoWrite().is_read_only() is False
