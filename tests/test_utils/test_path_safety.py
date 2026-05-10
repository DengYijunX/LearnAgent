import pytest
from pathlib import Path
from src.utils.path_safety import safe_path, safe_write


def test_safe_path_within_base(tmp_path):
    base = str(tmp_path)
    result = safe_path(base, "subdir/file.txt")
    assert str(result).startswith(str(Path(base).resolve()))


def test_safe_path_blocks_traversal(tmp_path):
    base = str(tmp_path)
    with pytest.raises(ValueError, match="路径穿越"):
        safe_path(base, "../escape.txt")


def test_safe_path_blocks_absolute(tmp_path):
    with pytest.raises(ValueError, match="路径穿越"):
        safe_path(str(tmp_path), "/etc/passwd")


def test_safe_path_creates_base(tmp_path):
    base = str(tmp_path / "new_base")
    result = safe_path(base, "file.txt")
    assert result.parent.exists()


def test_safe_write(tmp_path):
    path = tmp_path / "test.txt"
    safe_write(path, "hello world")
    assert path.read_text() == "hello world"


def test_safe_write_overwrite(tmp_path):
    path = tmp_path / "test.txt"
    safe_write(path, "first")
    safe_write(path, "second")
    assert path.read_text() == "second"
