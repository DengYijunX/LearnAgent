"""Manual smoke test for public GitHub README analysis."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.config.settings import load_settings
from app.tools.github_repo_analyzer import GitHubRepoAnalyzerTool


async def main() -> int:
    settings = load_settings()
    if not settings.run_real_tests and os.getenv("RUN_REAL_TESTS") != "1":
        print("跳过真实 GitHub README smoke test：请设置 RUN_REAL_TESTS=1。")
        return 0

    repo_url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "https://github.com/pallets/flask"
    )
    result = await GitHubRepoAnalyzerTool(max_chars=1200).call(
        {"repo_url": repo_url},
        context={},
    )
    if result.is_error:
        print(result.content)
        return 1
    print(result.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
