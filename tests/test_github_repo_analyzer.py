import pytest

from app.tools.github_repo_analyzer import GitHubRepoAnalyzerTool


@pytest.mark.asyncio
async def test_github_repo_analyzer_reads_public_readme_from_main_branch():
    async def fake_fetch(url: str, timeout: int):
        assert timeout == 10
        if url.endswith("/main/README.md"):
            return (
                b"# Demo Project\n\nA tiny project for learning agents.\n\n## Install\nUse Python.",
                "text/markdown; charset=utf-8",
            )
        raise RuntimeError("not found")

    tool = GitHubRepoAnalyzerTool(fetcher=fake_fetch)

    result = await tool.call(
        {"repo_url": "https://github.com/example/demo"},
        context={},
    )

    assert result.is_error is False
    assert "example/demo" in result.content
    assert "Demo Project" in result.content
    assert "A tiny project for learning agents." in result.content
    assert result.metadata["source"] == "real"
    assert result.metadata["owner"] == "example"
    assert result.metadata["repo"] == "demo"
    assert result.metadata["readme_url"].endswith("/main/README.md")


@pytest.mark.asyncio
async def test_github_repo_analyzer_falls_back_to_master_branch():
    attempted_urls = []

    async def fake_fetch(url: str, timeout: int):
        attempted_urls.append(url)
        if url.endswith("/master/README.md"):
            return (b"# Master README\n\nFallback branch content.", "text/markdown")
        raise RuntimeError("not found")

    tool = GitHubRepoAnalyzerTool(fetcher=fake_fetch)

    result = await tool.call(
        {"repo_url": "https://github.com/example/demo"},
        context={},
    )

    assert result.is_error is False
    assert "Master README" in result.content
    assert attempted_urls[0].endswith("/main/README.md")
    assert attempted_urls[1].endswith("/master/README.md")


@pytest.mark.asyncio
async def test_github_repo_analyzer_rejects_non_github_url():
    tool = GitHubRepoAnalyzerTool()

    result = await tool.call({"repo_url": "https://example.com/repo"}, context={})

    assert result.is_error is True
    assert "GitHub" in result.content


@pytest.mark.asyncio
async def test_github_repo_analyzer_reports_readme_fetch_failure():
    async def fake_fetch(url: str, timeout: int):
        raise RuntimeError("not found")

    tool = GitHubRepoAnalyzerTool(fetcher=fake_fetch)

    result = await tool.call(
        {"repo_url": "https://github.com/example/demo"},
        context={},
    )

    assert result.is_error is True
    assert "README" in result.content
    assert result.metadata["source"] == "real"
    assert result.metadata["owner"] == "example"
