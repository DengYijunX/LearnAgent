"""Public GitHub README analyzer without GitHub API access."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import re
from typing import Any, Awaitable, Callable
from urllib import request as urllib_request
from urllib.parse import urlparse

from app.tools.base import Tool, ToolResult


FetchResult = tuple[bytes, str]
Fetcher = Callable[[str, int], Awaitable[FetchResult]]


class GitHubRepoAnalyzerTool(Tool):
    name = "github_repo_analyzer"
    description = "Read a public GitHub repository README and summarize its learning value."
    input_schema = {
        "type": "object",
        "properties": {"repo_url": {"type": "string"}},
        "required": ["repo_url"],
    }

    def __init__(
        self,
        fetcher: Fetcher | None = None,
        timeout: int = 10,
        max_chars: int = 6000,
    ):
        self._fetcher = fetcher or _default_fetch
        self._timeout = timeout
        self._max_chars = max_chars

    async def call(self, tool_input: dict[str, Any], context: dict[str, Any]) -> ToolResult:
        repo_url = tool_input.get("repo_url", "")
        repo_ref = _parse_github_repo_url(repo_url)
        if repo_ref is None:
            return ToolResult(
                content="只支持公开 GitHub 仓库 URL，例如 https://github.com/owner/repo。",
                is_error=True,
                metadata={"repo_url": repo_url},
            )

        errors: list[str] = []
        for readme_url in _candidate_readme_urls(repo_ref):
            try:
                body, content_type = await self._fetcher(readme_url, self._timeout)
            except Exception as exc:
                errors.append(f"{readme_url}: {exc}")
                continue

            text = body.decode(_encoding_from_content_type(content_type) or "utf-8", errors="replace")
            title = _extract_markdown_title(text) or repo_ref.full_name
            content = _build_repo_summary(repo_ref, title, text[: self._max_chars])
            return ToolResult(
                content=content,
                metadata={
                    "source": "real",
                    "owner": repo_ref.owner,
                    "repo": repo_ref.repo,
                    "repo_url": repo_url,
                    "readme_url": readme_url,
                    "content_type": content_type,
                    "truncated": len(text) > self._max_chars,
                },
            )

        return ToolResult(
            content="未能读取公开 README。请确认仓库存在、可公开访问，并且包含 main/master 分支的 README.md。",
            is_error=True,
            metadata={
                "source": "real",
                "owner": repo_ref.owner,
                "repo": repo_ref.repo,
                "repo_url": repo_url,
                "errors": errors,
            },
        )


@dataclass(frozen=True)
class _RepoRef:
    owner: str
    repo: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


def _parse_github_repo_url(repo_url: str) -> _RepoRef | None:
    parsed = urlparse(repo_url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != "github.com":
        return None
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        return None
    owner = parts[0].strip()
    repo = parts[1].strip()
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not _is_safe_repo_part(owner) or not _is_safe_repo_part(repo):
        return None
    return _RepoRef(owner=owner, repo=repo)


def _candidate_readme_urls(repo_ref: _RepoRef) -> list[str]:
    return [
        f"https://raw.githubusercontent.com/{repo_ref.owner}/{repo_ref.repo}/main/README.md",
        f"https://raw.githubusercontent.com/{repo_ref.owner}/{repo_ref.repo}/master/README.md",
    ]


def _build_repo_summary(repo_ref: _RepoRef, title: str, readme_text: str) -> str:
    normalized = _normalize_markdown_text(readme_text)
    excerpt = normalized[:1200]
    return (
        f"仓库：{repo_ref.full_name}\n"
        f"标题：{title}\n"
        "README 摘要：\n"
        f"{excerpt}\n\n"
        "学习建议：\n"
        "1. 先阅读 README 的项目目标、安装方式和最小示例。\n"
        "2. 再查看快速开始、核心概念和示例目录。\n"
        "3. 如果要深入学习，下一步可以结合依赖文件和源码目录继续分析。"
    )


def _extract_markdown_title(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def _normalize_markdown_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _is_safe_repo_part(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]+", value))


def _encoding_from_content_type(content_type: str) -> str | None:
    match = re.search(r"charset=([^;]+)", content_type, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


async def _default_fetch(url: str, timeout: int) -> FetchResult:
    return await asyncio.to_thread(_fetch_blocking, url, timeout)


def _fetch_blocking(url: str, timeout: int) -> FetchResult:
    req = urllib_request.Request(
        url=url,
        headers={"User-Agent": "LearnAgent/0.1"},
        method="GET",
    )
    with urllib_request.urlopen(req, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        return response.read(), content_type
