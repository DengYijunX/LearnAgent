import os
from src.tools.filesystem import create_project, write_file


def test_create_project(temp_dir):
    project_path = create_project(str(temp_dir), "test-proj")
    assert os.path.exists(project_path)
    assert os.path.exists(os.path.join(project_path, "README.md"))


def test_write_file(temp_dir):
    project_path = create_project(str(temp_dir), "test-proj")
    file_path = write_file(project_path, "main.py", "print('hello')")
    assert os.path.exists(file_path)
    with open(file_path) as f:
        assert f.read() == "print('hello')"
