"""Mock learning tools for stage-one architecture verification."""

from __future__ import annotations

from typing import Any

from app.tools.base import Tool, ToolResult


class MockSearchWebTool(Tool):
    name = "search_web"
    description = "Mock search results for a learning topic."
    input_schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }

    async def call(self, tool_input: dict[str, Any], context: dict[str, Any]) -> ToolResult:
        query = tool_input.get("query", "")
        return ToolResult(
            content=f"[mock search] 与 {query} 相关的官方文档、教程和概念资料。",
            metadata={"source": "mock", "query": query},
        )


class MockReadUrlTool(Tool):
    name = "read_url"
    description = "Mock URL reader for documentation pages."
    input_schema = {
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    }

    async def call(self, tool_input: dict[str, Any], context: dict[str, Any]) -> ToolResult:
        url = tool_input.get("url", "")
        return ToolResult(
            content=f"[mock read_url] 已读取 {url} 的主要内容摘要。",
            metadata={"source": "mock", "title": "Mock page", "url": url},
        )


class MockGitHubRepoAnalyzerTool(Tool):
    name = "github_repo_analyzer"
    description = "Mock GitHub repository learning-value analyzer."
    input_schema = {
        "type": "object",
        "properties": {"repo_url": {"type": "string"}},
        "required": ["repo_url"],
    }

    async def call(self, tool_input: dict[str, Any], context: dict[str, Any]) -> ToolResult:
        repo_url = tool_input.get("repo_url", "")
        return ToolResult(
            content=f"[mock repo] {repo_url} 的 README、目录结构和学习价值摘要。",
            metadata={"source": "mock", "repo_url": repo_url},
        )
