"""Tests for workspace file and code execution tools."""

import os
import sys
import tempfile

import pytest


class TestFileWrite:
    @pytest.mark.asyncio
    async def test_writes_file_in_workspace(self, workspace):
        from app.tools.workspace_tools import FileWrite

        tool = FileWrite(workspace_root=workspace)
        result = await tool.call({"path": "test_write.py", "content": "print('hello')"})
        assert result.get("isError") is False
        assert os.path.exists(os.path.join(workspace, "test_write.py"))

    @pytest.mark.asyncio
    async def test_creates_subdirectories(self, workspace):
        from app.tools.workspace_tools import FileWrite

        tool = FileWrite(workspace_root=workspace)
        result = await tool.call({"path": "src/utils/helpers.py", "content": "# helpers"})
        assert result.get("isError") is False
        assert os.path.exists(os.path.join(workspace, "src", "utils", "helpers.py"))

    @pytest.mark.asyncio
    async def test_rejects_path_traversal(self, workspace):
        from app.tools.workspace_tools import FileWrite

        tool = FileWrite(workspace_root=workspace)
        result = await tool.call({"path": "../../etc/passwd", "content": "bad"})
        assert result.get("isError") is True

    @pytest.mark.asyncio
    async def test_rejects_absolute_path(self, workspace):
        from app.tools.workspace_tools import FileWrite

        tool = FileWrite(workspace_root=workspace)
        result = await tool.call({"path": "C:/windows/system32/test.txt", "content": "bad"})
        assert result.get("isError") is True

    def test_is_not_read_only(self):
        from app.tools.workspace_tools import FileWrite

        assert FileWrite(workspace_root="/tmp").is_read_only() is False


class TestFileRead:
    @pytest.mark.asyncio
    async def test_reads_existing_file(self, workspace):
        from app.tools.workspace_tools import FileRead

        path = os.path.join(workspace, "test.py")
        with open(path, "w") as f:
            f.write("x = 42")
        tool = FileRead(workspace_root=workspace)
        result = await tool.call({"path": "test.py"})
        assert result.get("isError") is False
        assert "x = 42" in result["content"]

    def test_is_read_only(self):
        from app.tools.workspace_tools import FileRead

        assert FileRead(workspace_root="/tmp").is_read_only() is True


class TestRunCode:
    @pytest.mark.asyncio
    async def test_runs_python_code(self, workspace):
        from app.tools.workspace_tools import RunCode

        with open(os.path.join(workspace, "hello.py"), "w") as f:
            f.write("print('hello from learnagent')")
        tool = RunCode(workspace_root=workspace, timeout=10)
        result = await tool.call({"command": "python hello.py"})
        assert result.get("isError") is False
        assert "hello" in result.get("stdout", "")

    @pytest.mark.asyncio
    async def test_captures_stderr(self, workspace):
        from app.tools.workspace_tools import RunCode

        with open(os.path.join(workspace, "err.py"), "w") as f:
            f.write("import sys; sys.stderr.write('error msg')")
        tool = RunCode(workspace_root=workspace, timeout=10)
        result = await tool.call({"command": "python err.py"})
        assert "error msg" in result.get("stderr", "")

    @pytest.mark.skipif(sys.platform == "win32", reason="Windows subprocess timeout behavior differs")
    @pytest.mark.asyncio
    async def test_timeout_kills_process(self, workspace):
        from app.tools.workspace_tools import RunCode

        with open(os.path.join(workspace, "slow.py"), "w") as f:
            f.write("import time; time.sleep(30)")
        tool = RunCode(workspace_root=workspace, timeout=2)
        result = await tool.call({"command": "python slow.py"})
        assert result.get("isError") is True
        assert "timeout" in str(result).lower()

    def test_is_not_read_only(self):
        from app.tools.workspace_tools import RunCode

        assert RunCode(workspace_root="/tmp").is_read_only() is False


@pytest.fixture
def workspace():
    with tempfile.TemporaryDirectory() as d:
        yield d
