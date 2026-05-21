"""Tests for memory/session_store.py and memory/memory_store.py."""

import os
import tempfile


class TestSessionStore:
    def test_append_and_read_messages(self, session_store):
        session_store.append_message("s1", {"role": "user", "content": "hello"})
        session_store.append_message("s1", {"role": "assistant", "content": "hi"})
        messages = session_store.get_messages("s1")
        assert len(messages) == 2

    def test_empty_session_returns_empty_list(self, session_store):
        messages = session_store.get_messages("nonexistent")
        assert messages == []

    def test_multiple_sessions_isolated(self, session_store):
        session_store.append_message("s1", {"role": "user", "content": "a"})
        session_store.append_message("s2", {"role": "user", "content": "b"})
        assert len(session_store.get_messages("s1")) == 1
        assert len(session_store.get_messages("s2")) == 1


class TestMemoryStore:
    def test_save_and_load_memory(self, memory_store):
        memory_store.save(
            name="test_config",
            memory_type="project",
            description="测试配置",
            body="- key: value\n",
        )
        found = memory_store.find("test_config")
        assert found is not None
        assert found["name"] == "test_config"
        assert found["type"] == "project"

    def test_find_nonexistent_returns_none(self, memory_store):
        assert memory_store.find("no_such_memory") is None

    def test_list_by_type(self, memory_store):
        memory_store.save("m1", "project", "p1", "- a\n")
        memory_store.save("m2", "user", "u1", "- b\n")
        projects = memory_store.list_by_type("project")
        assert len(projects) == 1
        assert projects[0]["name"] == "m1"

    def test_overwrite_existing(self, memory_store):
        memory_store.save("m1", "project", "v1", "- a\n")
        memory_store.save("m1", "project", "v2", "- b\n")
        found = memory_store.find("m1")
        assert found["description"] == "v2"


import pytest


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def session_store(tmp_dir):
    from app.memory.session_store import SessionStore

    return SessionStore(base_dir=tmp_dir)


@pytest.fixture
def memory_store(tmp_dir):
    from app.memory.memory_store import MemoryStore

    return MemoryStore(base_dir=tmp_dir)
