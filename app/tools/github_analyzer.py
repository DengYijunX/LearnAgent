"""GitHub 仓库分析工具 —— 读取 README 和项目结构。"""

import re

from app.tools.base import Tool

GITHUB_URL_PATTERN = re.compile(r"github\.com/([\w\-\.]+)/([\w\-\.]+)")


def parse_repo_url(url: str) -> tuple[str, str] | None:
    """Extract (owner, repo) from a GitHub URL."""
    match = GITHUB_URL_PATTERN.search(url)
    if not match:
        return None
    return match.group(1), match.group(2).rstrip("/")


class MockGitHubAnalyzer(Tool):
    name = "analyze_github_repo"
    description = "分析 GitHub 仓库的 README、项目结构、技术栈和学习价值。输入 repo_url。"
    input_schema = {
        "type": "object",
        "properties": {
            "repo_url": {
                "type": "string",
                "description": "GitHub 仓库完整 URL，如 https://github.com/owner/repo",
            }
        },
        "required": ["repo_url"],
    }

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        url = tool_input.get("repo_url", "")
        parsed = parse_repo_url(url)
        if not parsed:
            return {"isError": True, "error": "无法解析 GitHub URL，请提供完整的仓库地址。"}
        owner, repo = parsed
        return {
            "content": (
                f"[Mock 仓库分析] {owner}/{repo}\n\n"
                f"## README 摘要\n"
                f"这是 {repo} 项目的 README 内容（mock）。"
                f"该仓库由 {owner} 维护。\n\n"
                f"## 目录结构（mock）\n"
                f"- src/\n- tests/\n- docs/\n- pyproject.toml\n- README.md\n\n"
                f"## 学习建议\n"
                f"1. 先读 README 了解项目目标\n"
                f"2. 查看核心模块的入口文件\n"
                f"3. 运行示例代码理解用法\n"
                f"4. 从简单的 issue 开始贡献"
            ),
            "metadata": {"owner": owner, "repo": repo, "url": url},
            "isError": False,
        }


class RealGitHubAnalyzer(Tool):
    name = "analyze_github_repo"
    description = "读取 GitHub 仓库的 README、目录结构，分析技术栈和学习价值。输入 repo_url。"
    input_schema = {
        "type": "object",
        "properties": {
            "repo_url": {
                "type": "string",
                "description": "GitHub 仓库完整 URL，如 https://github.com/owner/repo",
            }
        },
        "required": ["repo_url"],
    }

    def __init__(self, timeout: int = 20):
        self._timeout = timeout

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        url = (tool_input.get("repo_url") or "").strip()
        parsed = parse_repo_url(url)
        if not parsed:
            return {"isError": True, "error": "无法解析 GitHub URL。"}
        owner, repo = parsed

        try:
            import httpx

            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "LearnAgent/0.1",
                    "Accept": "text/plain,text/html,application/json",
                }

                # 1. 读取 README
                readme_content = await self._fetch_readme(client, owner, repo, headers)

                # 2. 读取仓库信息（无需 token 的公开 API）
                repo_info = await self._fetch_repo_info(client, owner, repo, headers)

            if readme_content == "(未找到 README.md)" and repo_info is None:
                return {"isError": True, "error": f"仓库 {owner}/{repo} 不存在或无法访问。"}

            content = self._build_analysis(owner, repo, url, readme_content, repo_info)
            return {
                "content": content,
                "metadata": {"owner": owner, "repo": repo, "url": url},
                "isError": False,
            }
        except Exception as e:
            return {"isError": True, "error": f"仓库分析失败：{e}"}

    async def _fetch_readme(self, client, owner: str, repo: str, headers: dict) -> str:
        """Try multiple branches to fetch README."""
        for branch in ("main", "master"):
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
            try:
                r = await client.get(raw_url, headers=headers)
                if r.status_code == 200:
                    text = r.text
                    if len(text) > 5000:
                        text = text[:5000] + f"\n...(截断，原文共 {len(text)} 字符)"
                    return text
            except Exception:
                continue
        return "(未找到 README.md)"

    async def _fetch_repo_info(self, client, owner: str, repo: str, headers: dict) -> dict | None:
        """Fetch repo metadata from GitHub API (no auth needed for public repos)."""
        try:
            r = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers={**headers, "Accept": "application/vnd.github+json"},
            )
            if r.status_code == 200:
                data = r.json()
                return {
                    "description": data.get("description", ""),
                    "language": data.get("language", ""),
                    "stars": data.get("stargazers_count", 0),
                    "topics": data.get("topics", []),
                }
        except Exception:
            pass
        return None

    def _build_analysis(self, owner: str, repo: str, url: str, readme: str, info: dict | None) -> str:
        parts = [f"# {owner}/{repo} 仓库分析\n"]
        parts.append(f"链接：{url}\n")

        if info:
            if info.get("description"):
                parts.append(f"**项目描述：** {info['description']}\n")
            if info.get("language"):
                parts.append(f"**主要语言：** {info['language']}")
            if info.get("stars"):
                parts.append(f"**Star 数：** {info['stars']}")
            if info.get("topics"):
                parts.append(f"**主题标签：** {', '.join(info['topics'])}")
            if info:
                parts.append("")

        parts.append("## README\n")
        parts.append(readme)
        return "\n".join(parts)
