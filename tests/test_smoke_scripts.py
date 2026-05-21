import os
import subprocess
import sys
from pathlib import Path


def test_smoke_llm_real_script_skips_without_real_test_flag():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["RUN_REAL_TESTS"] = "0"

    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "smoke_llm_real.py")],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0
    assert "跳过真实 LLM smoke test" in result.stdout


def test_smoke_agent_real_script_skips_without_real_test_flag():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["RUN_REAL_TESTS"] = "0"

    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "smoke_agent_real.py")],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0
    assert "跳过真实 Agent smoke test" in result.stdout


def test_smoke_read_url_real_script_skips_without_real_test_flag():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["RUN_REAL_TESTS"] = "0"

    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "smoke_read_url_real.py")],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0
    assert "跳过真实 ReadUrl smoke test" in result.stdout


def test_smoke_github_repo_real_script_skips_without_real_test_flag():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["RUN_REAL_TESTS"] = "0"

    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "smoke_github_repo_real.py")],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0
    assert "跳过真实 GitHub README smoke test" in result.stdout
