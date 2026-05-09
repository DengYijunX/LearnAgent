# LearnAgent 实现计划

> **面向 agent 执行者：** 必须使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现。步骤使用 `- [ ]` 语法跟踪进度。

**目标：** 构建一个 AI 学习助手，帮助用户通过按需对话、场景化教学项目和定时推送完成 "发现新技术 → 理解核心概念 → 动手实践" 的学习闭环。

**架构：** FastAPI 作为应用骨架。LangGraph 编排 agent 决策流（Router → ReAct / Plan-Execute 双路径）。工具层是普通 async 函数，被 agent graph 调用。记忆层从 LangGraph State 起步（工作记忆），渐进式接入 SQLite + ChromaDB（短期记忆）和 JSON 文件（用户画像）。单进程运行，CLI 为主要交互入口。

**技术栈：** Python 3.11+, LangGraph, FastAPI, structlog, ChromaDB, SQLite, pytest + pytest-asyncio, Claude API

---

## 文件结构

```
agent/
├── .env.example                  # API Key 等配置模板
├── .gitignore
├── Makefile                      # install / run / test / lint
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── config.py                 # 环境变量配置
│   ├── logging_config.py         # structlog 初始化
│   ├── main.py                   # FastAPI app + CLI 入口
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic 请求/响应模型
│   ├── router/
│   │   ├── __init__.py
│   │   └── router.py             # LLM 驱动的任务分类
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── react_agent.py        # 简单任务 ReAct 循环
│   │   └── plan_execute_agent.py # 复杂任务 Plan-then-Execute（LangGraph）
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── web_search.py         # Tavily 搜索
│   │   ├── content_fetch.py      # Jina AI Reader 内容抓取
│   │   ├── github_disco.py       # GitHub Trending + 仓库搜索
│   │   ├── filesystem.py         # 本地项目脚手架
│   │   └── notify.py             # Cron + Slack Webhook
│   └── memory/
│       ├── __init__.py
│       ├── working.py            # LangGraph State 封装
│       ├── short_term.py         # SQLite + ChromaDB
│       └── user_profile.py       # JSON 用户画像
└── tests/
    ├── __init__.py
    ├── conftest.py               # Mock LLM, 共享 fixtures
    ├── test_router.py
    ├── test_react_agent.py
    ├── test_plan_execute_agent.py
    ├── test_tools/
    │   ├── __init__.py
    │   ├── test_web_search.py
    │   ├── test_content_fetch.py
    │   ├── test_github_disco.py
    │   ├── test_filesystem.py
    │   └── test_notify.py
    └── test_memory/
        ├── __init__.py
        ├── test_working.py
        ├── test_short_term.py
        └── test_user_profile.py
```

---

## 阶段一：项目脚手架（P0 前置）

### 任务 1：创建 pyproject.toml 和 .env.example

**文件：**
- 创建：`pyproject.toml`
- 创建：`.env.example`

- [ ] **步骤 1：编写 pyproject.toml**

```toml
[project]
name = "learnagent"
version = "0.1.0"
description = "AI 学习助手 Agent"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "langgraph>=0.2.0",
    "langchain-core>=0.3.0",
    "langchain-anthropic>=0.2.0",
    "tavily-python>=0.5.0",
    "httpx>=0.27.0",
    "chromadb>=0.5.0",
    "structlog>=24.4.0",
    "pydantic>=2.8.0",
    "pydantic-settings>=2.3.0",
    "aiosqlite>=0.20.0",
    "apscheduler>=3.10.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.6.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "integration: 需要真实 API 调用的集成测试",
]

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **步骤 2：编写 .env.example**

```bash
# LLM
ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_MODEL_SIMPLE=claude-sonnet-4-6
ANTHROPIC_MODEL_COMPLEX=claude-opus-4-7

# 搜索
TAVILY_API_KEY=tvly-xxx

# Jina AI Reader（可选，没有也能用 httpx 抓取）
JINA_API_KEY=jina_xxx

# GitHhub（可选，公开仓库不需要 token 也能搜，但有 token 速率更高）
GITHUB_TOKEN=ghp_xxx

# 通知
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx

# 日志
LOG_LEVEL=DEBUG
```

- [ ] **步骤 3：验证**

运行：`python -c "import pyproject_toml; print('ok')" 2>&1 || echo "expected: pyproject.toml 创建成功即可"`

- [ ] **步骤 4：提交**

```bash
git add pyproject.toml .env.example
git commit -m "初始化项目：添加 pyproject.toml 和 .env.example"
```

---

### 任务 2：创建 Makefile

**文件：**
- 创建：`Makefile`

- [ ] **步骤 1：编写 Makefile**

```makefile
.PHONY: install run test lint clean

install:
	pip install -e ".[dev]"

run:
	python -m src.main

test:
	pytest -v

test-cov:
	pytest -v --cov=src --cov-report=term-missing

test-integration:
	pytest -v -m "integration"

lint:
	ruff check src/ tests/

clean:
	rm -rf __pycache__ .pytest_cache .coverage
	find src -name '__pycache__' -exec rm -rf {} +
	find tests -name '__pycache__' -exec rm -rf {} +
```

- [ ] **步骤 2：验证**

运行：`make` 应输出 "No targets specified" 或类似提示（Makefile 存在即可）

- [ ] **步骤 3：提交**

```bash
git add Makefile
git commit -m "添加 Makefile：install / run / test / lint 统一入口"
```

---

### 任务 3：创建配置和日志模块

**文件：**
- 创建：`src/__init__.py`（空文件）
- 创建：`src/config.py`
- 创建：`src/logging_config.py`
- 测试：`tests/__init__.py`（空文件）
- 测试：`tests/conftest.py`

- [ ] **步骤 1：编写测试 — conftest.py**

```python
import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def mock_llm_response():
    """返回 Mock LLM 的工厂函数"""
    def _make(text: str):
        mock = AsyncMock()
        mock.ainvoke.return_value = type("msg", (), {"content": text})()
        return mock
    return _make


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path
```

- [ ] **步骤 2：运行测试确认失败（因为 src 还没写）**

运行：`pytest tests/conftest.py -v`
预期：PASS（conftest 无 import 依赖，应该通过）

- [ ] **步骤 3：编写 config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    anthropic_model_simple: str = "claude-sonnet-4-6"
    anthropic_model_complex: str = "claude-opus-4-7"

    tavily_api_key: str = ""
    jina_api_key: str = ""
    github_token: str = ""

    slack_webhook_url: str = ""

    log_level: str = "DEBUG"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

- [ ] **步骤 4：编写 logging_config.py**

```python
import structlog
import logging
from src.config import settings


def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer() if settings.log_level == "DEBUG"
            else structlog.processors.JSONRenderer(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    level = getattr(logging, settings.log_level.upper(), logging.DEBUG)
    logging.basicConfig(format="%(message)s", level=level)

    return structlog.get_logger()
```

- [ ] **步骤 5：编写测试 — test_config.py**

先创建 `tests/test_config.py`：

```python
import os
from src.config import Settings


def test_settings_defaults():
    s = Settings()
    assert s.log_level == "DEBUG"
    assert s.anthropic_model_simple == "claude-sonnet-4-6"


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    s = Settings()
    assert s.log_level == "INFO"
```

运行：`pytest tests/test_config.py -v`
预期：PASS

- [ ] **步骤 6：提交**

```bash
git add src/__init__.py src/config.py src/logging_config.py tests/
git commit -m "添加配置模块和日志模块（pydantic-settings + structlog）"
```

---

## 阶段二：P0 — 按需对话学习

### 任务 4：定义 Pydantic 数据模型

**文件：**
- 创建：`src/models/__init__.py`
- 创建：`src/models/schemas.py`
- 测试：`tests/test_models.py`

- [ ] **步骤 1：编写测试 — tests/test_models.py**

```python
from src.models.schemas import UserInput, TaskType, KnowledgeSummary


def test_user_input_parsing():
    ui = UserInput(query="什么是 RAG")
    assert ui.query == "什么是 RAG"
    assert ui.input_type == "keyword"  # 默认推断


def test_user_input_with_url():
    ui = UserInput(query="https://github.com/langchain-ai/langgraph")
    assert ui.input_type == "github_url"


def test_user_input_with_doc_url():
    ui = UserInput(query="https://docs.python.org/3/library/asyncio.html")
    assert ui.input_type == "doc_url"


def test_task_type_enum():
    assert TaskType.SIMPLE.value == "simple"
    assert TaskType.COMPLEX.value == "complex"


def test_knowledge_summary():
    ks = KnowledgeSummary(
        topic="RAG",
        core_concepts=["检索", "增强", "生成"],
        learning_points=["向量数据库的选择", "Embedding 的作用"],
        related_techs=["LangChain", "LlamaIndex", "向量数据库"],
    )
    assert len(ks.core_concepts) == 3
```

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_models.py -v`
预期：FAIL（模块不存在）

- [ ] **步骤 3：编写 schemas.py**

```python
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class TaskType(str, Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"


class InputType(str, Enum):
    KEYWORD = "keyword"
    GITHUB_URL = "github_url"
    DOC_URL = "doc_url"
    UNKNOWN = "unknown"


class UserInput(BaseModel):
    query: str = Field(..., description="用户输入的技术名称/链接/仓库地址")

    @property
    def input_type(self) -> InputType:
        q = self.query.strip()
        if q.startswith("https://github.com/"):
            return InputType.GITHUB_URL
        if q.startswith("http://") or q.startswith("https://"):
            return InputType.DOC_URL
        return InputType.KEYWORD


class RouterDecision(BaseModel):
    task_type: TaskType
    reason: str = ""


class KnowledgeSummary(BaseModel):
    topic: str
    core_concepts: list[str] = Field(default_factory=list)
    learning_points: list[str] = Field(default_factory=list)
    related_techs: list[str] = Field(default_factory=list)
```

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_models.py -v`
预期：PASS（4 passed）

- [ ] **步骤 5：提交**

```bash
git add src/models/ tests/test_models.py
git commit -m "添加 Pydantic 数据模型：UserInput / RouterDecision / KnowledgeSummary"
```

---

### 任务 5：实现 Tavily Web Search 工具

**文件：**
- 创建：`src/tools/__init__.py`
- 创建：`src/tools/web_search.py`
- 测试：`tests/test_tools/__init__.py`
- 测试：`tests/test_tools/test_web_search.py`

- [ ] **步骤 1：编写测试**

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.tools.web_search import web_search


@pytest.mark.asyncio
async def test_web_search_returns_results():
    mock_response = {
        "results": [
            {"title": "RAG 入门", "url": "https://example.com/rag", "content": "RAG 是检索增强生成..."}
        ]
    }
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = lambda: None
        results = await web_search("什么是 RAG")
        assert len(results) == 1
        assert results[0]["title"] == "RAG 入门"


@pytest.mark.asyncio
async def test_web_search_empty_query_returns_empty():
    results = await web_search("")
    assert results == []
```

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_tools/test_web_search.py -v`
预期：FAIL（模块不存在）

- [ ] **步骤 3：编写 web_search.py**

```python
import httpx
from src.config import settings
from src.logging_config import setup_logging

logger = setup_logging()

TAVILY_API_URL = "https://api.tavily.com/search"


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    使用 Tavily API 搜索技术资料。
    返回: [{"title": ..., "url": ..., "content": ...}, ...]
    """
    if not query.strip():
        logger.warning("web_search: 空查询")
        return []

    logger.debug("web_search 开始", query=query)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                TAVILY_API_URL,
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            logger.info("web_search 完成", query=query, result_count=len(results))
            return [
                {"title": r["title"], "url": r["url"], "content": r["content"]}
                for r in results
            ]
    except Exception as e:
        logger.error("web_search 失败", query=query, error=str(e))
        return []
```

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_tools/test_web_search.py -v`
预期：PASS（2 passed）

- [ ] **步骤 5：提交**

```bash
git add src/tools/__init__.py src/tools/web_search.py tests/test_tools/
git commit -m "添加 Web Search 工具：Tavily API 封装"
```

---

### 任务 6：实现 Content Fetch 工具

**文件：**
- 创建：`src/tools/content_fetch.py`
- 测试：`tests/test_tools/test_content_fetch.py`

- [ ] **步骤 1：编写测试**

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.tools.content_fetch import fetch_content


@pytest.mark.asyncio
async def test_fetch_content_returns_markdown():
    mock_response = AsyncMock()
    mock_response.text = "<html><body><article>RAG 简介</article></body></html>"
    mock_response.raise_for_status = lambda: None
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        result = await fetch_content("https://example.com/rag")
        assert "RAG 简介" in result.content
        assert result.url == "https://example.com/rag"


@pytest.mark.asyncio
async def test_fetch_content_invalid_url():
    result = await fetch_content("")
    assert result.content == ""
    assert result.url == ""
```

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_tools/test_content_fetch.py -v`
预期：FAIL（模块不存在）

- [ ] **步骤 3：编写 content_fetch.py**

```python
import httpx
from pydantic import BaseModel
from src.config import settings
from src.logging_config import setup_logging

logger = setup_logging()

JINA_READER_URL = "https://r.jina.ai/http://{url}"


class FetchedContent(BaseModel):
    url: str = ""
    title: str = ""
    content: str = ""


async def fetch_content(url: str) -> FetchedContent:
    """使用 Jina AI Reader 抓取网页内容转 Markdown。降级方案：直接用 httpx 抓取。"""
    if not url.strip():
        return FetchedContent()

    logger.debug("fetch_content 开始", url=url)
    try:
        jina_url = f"https://r.jina.ai/{url}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                jina_url,
                headers={"Authorization": f"Bearer {settings.jina_api_key}"}
                if settings.jina_api_key else {},
            )
            resp.raise_for_status()
            logger.info("fetch_content 完成", url=url, length=len(resp.text))
            return FetchedContent(url=url, content=resp.text)
    except Exception:
        # 降级：直接抓取 HTML
        logger.warning("Jina Reader 失败，降级为直接抓取", url=url)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, headers={"User-Agent": "LearnAgent/1.0"})
                resp.raise_for_status()
                return FetchedContent(url=url, content=resp.text[:10000])
        except Exception as e:
            logger.error("fetch_content 失败", url=url, error=str(e))
            return FetchedContent(url=url, content="")
```

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_tools/test_content_fetch.py -v`
预期：PASS（2 passed）

- [ ] **步骤 5：提交**

```bash
git add src/tools/content_fetch.py tests/test_tools/test_content_fetch.py
git commit -m "添加 Content Fetch 工具：Jina AI Reader + httpx 降级"
```

---

### 任务 7：实现 GitHub Discovery 工具

**文件：**
- 创建：`src/tools/github_disco.py`
- 测试：`tests/test_tools/test_github_disco.py`

- [ ] **步骤 1：编写测试**

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.tools.github_disco import search_github_repos, get_github_trending


@pytest.mark.asyncio
async def test_search_github_repos():
    mock_response = {"items": [
        {"full_name": "test/repo", "description": "测试仓库", "html_url": "https://github.com/test/repo", "stargazers_count": 100}
    ]}
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status = lambda: None
        results = await search_github_repos("langgraph")
        assert len(results) == 1
        assert results[0]["full_name"] == "test/repo"


@pytest.mark.asyncio
async def test_get_github_trending():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json.return_value = {"items": []}
        mock_get.return_value.raise_for_status = lambda: None
        results = await get_github_trending()
        assert isinstance(results, list)
```

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_tools/test_github_disco.py -v`
预期：FAIL

- [ ] **步骤 3：编写 github_disco.py**

```python
import httpx
from src.config import settings
from src.logging_config import setup_logging

logger = setup_logging()

GITHUB_API = "https://api.github.com"


async def search_github_repos(query: str, per_page: int = 5) -> list[dict]:
    """搜索 GitHub 仓库"""
    if not query.strip():
        return []

    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    logger.debug("github_search 开始", query=query)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{GITHUB_API}/search/repositories",
                params={"q": query, "sort": "stars", "per_page": per_page},
                headers=headers,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            logger.info("github_search 完成", query=query, count=len(items))
            return [
                {
                    "full_name": item["full_name"],
                    "description": item.get("description", ""),
                    "html_url": item["html_url"],
                    "stargazers_count": item.get("stargazers_count", 0),
                    "language": item.get("language", ""),
                }
                for item in items
            ]
    except Exception as e:
        logger.error("github_search 失败", query=query, error=str(e))
        return []


async def get_github_trending(language: str = "") -> list[dict]:
    """获取 GitHub Trending（按今日创建时间排序的仓库）"""
    q = f"created:>$(date -d '7 days ago' +%Y-%m-%d)"
    if language:
        q += f" language:{language}"
    return await search_github_repos(q)
```

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_tools/test_github_disco.py -v`
预期：PASS（2 passed）

- [ ] **步骤 5：提交**

```bash
git add src/tools/github_disco.py tests/test_tools/test_github_disco.py
git commit -m "添加 GitHub Discovery 工具：仓库搜索 + Trending"
```

---

### 任务 8：实现 Router（任务分类器）

**文件：**
- 创建：`src/router/__init__.py`
- 创建：`src/router/router.py`
- 测试：`tests/test_router.py`

- [ ] **步骤 1：编写测试**

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.router.router import route_task
from src.models.schemas import UserInput, TaskType


@pytest.mark.asyncio
async def test_route_keyword_to_simple():
    """技术名词查询应路由到简单任务"""
    with patch("langchain_anthropic.ChatAnthropic", autospec=True) as MockLLM:
        mock_instance = MockLLM.return_value
        mock_msg = AsyncMock()
        mock_msg.content = '{"task_type": "simple", "reason": "这是一个概念问题"}'
        mock_instance.ainvoke = AsyncMock(return_value=mock_msg)
        decision = await route_task(UserInput(query="什么是 RAG"))
        assert decision.task_type == TaskType.SIMPLE


@pytest.mark.asyncio
async def test_route_learn_to_complex():
    """'我要学 X' 应路由到复杂任务"""
    with patch("langchain_anthropic.ChatAnthropic", autospec=True) as MockLLM:
        mock_instance = MockLLM.return_value
        mock_msg = AsyncMock()
        mock_msg.content = '{"task_type": "complex", "reason": "用户要学新技术，需要生成教学项目"}'
        mock_instance.ainvoke = AsyncMock(return_value=mock_msg)
        decision = await route_task(UserInput(query="我要学 Redis"))
        assert decision.task_type == TaskType.COMPLEX


@pytest.mark.asyncio
async def test_route_llm_error_fallback_to_simple():
    """LLM 调用失败时降级为简单任务"""
    with patch("langchain_anthropic.ChatAnthropic", autospec=True) as MockLLM:
        mock_instance = MockLLM.return_value
        mock_instance.ainvoke = AsyncMock(side_effect=Exception("API 错误"))
        decision = await route_task(UserInput(query="测试"))
        assert decision.task_type == TaskType.SIMPLE
        assert "fallback" in decision.reason.lower()
```

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_router.py -v`
预期：FAIL（router.py 不存在）

- [ ] **步骤 3：编写 router.py**

```python
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import settings
from src.models.schemas import UserInput, RouterDecision, TaskType
from src.logging_config import setup_logging

logger = setup_logging()

ROUTER_PROMPT = """你是一个任务路由器。判断用户输入属于哪种类型：

- **simple**：问概念、查资料、解释名词、搜索文档。只需搜索+总结。
- **complex**：表达"我要学X"、"帮我掌握X"、"带我做X项目"等学习意图。需要生成教学项目。

只返回 JSON：
{"task_type": "simple|complex", "reason": "一句话说明判断依据"}"""


async def route_task(user_input: UserInput) -> RouterDecision:
    """LLM 驱动的任务路由"""
    logger.debug("router 开始", query=user_input.query[:100])
    try:
        llm = ChatAnthropic(
            model=settings.anthropic_model_simple,
            api_key=settings.anthropic_api_key,
            max_tokens=200,
        )
        msgs = [
            SystemMessage(content=ROUTER_PROMPT),
            HumanMessage(content=user_input.query),
        ]
        response = await llm.ainvoke(msgs)
        content = response.content.strip()
        # 提取 JSON（兼容 LLM 可能包裹 ```json 的情况）
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)
        decision = RouterDecision(
            task_type=TaskType(data["task_type"]),
            reason=data.get("reason", ""),
        )
        logger.info("router 决策完成", query=user_input.query[:50], task_type=decision.task_type.value)
        return decision
    except Exception as e:
        logger.error("router 失败，降级为 simple", query=user_input.query[:50], error=str(e))
        return RouterDecision(task_type=TaskType.SIMPLE, reason="router fallback due to error")
```

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_router.py -v`
预期：PASS（3 passed）

- [ ] **步骤 5：提交**

```bash
git add src/router/ tests/test_router.py
git commit -m "添加 Router 任务分类器：LLM 驱动，失败降级为简单任务"
```

---

### 任务 9：实现 Agent 状态和工作记忆

**文件：**
- 创建：`src/agent/__init__.py`
- 创建：`src/memory/__init__.py`
- 创建：`src/memory/working.py`
- 测试：`tests/test_memory/__init__.py`
- 测试：`tests/test_memory/test_working.py`

- [ ] **步骤 1：编写测试**

```python
from src.memory.working import AgentState, create_initial_state


def test_create_initial_state():
    state = create_initial_state(user_query="什么是 RAG")
    assert state["user_query"] == "什么是 RAG"
    assert state["messages"] == []
    assert state["intermediate_steps"] == []
    assert state["final_answer"] == ""


def test_agent_state_append_message():
    state = create_initial_state(user_query="测试")
    state["messages"].append({"role": "assistant", "content": "你好"})
    assert len(state["messages"]) == 1


def test_agent_state_record_step():
    state = create_initial_state(user_query="测试")
    state["intermediate_steps"].append({"tool": "search", "result": "found 3 items"})
    assert len(state["intermediate_steps"]) == 1
```

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_memory/test_working.py -v`
预期：FAIL

- [ ] **步骤 3：编写 working.py**

```python
from typing import TypedDict, Annotated
from operator import add


class AgentState(TypedDict):
    """Agent 工作记忆。LangGraph 在节点间传递这个 state。"""
    user_query: str
    messages: Annotated[list[dict], add]
    intermediate_steps: Annotated[list[dict], add]
    final_answer: str
    error: str


def create_initial_state(user_query: str) -> AgentState:
    return AgentState(
        user_query=user_query,
        messages=[],
        intermediate_steps=[],
        final_answer="",
        error="",
    )
```

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_memory/test_working.py -v`
预期：PASS（3 passed）

- [ ] **步骤 5：提交**

```bash
git add src/memory/ src/agent/__init__.py tests/test_memory/
git commit -m "添加 Agent 工作记忆：LangGraph TypedDict State"
```

---

### 任务 10：实现 ReAct Agent（简单任务路径）

**文件：**
- 创建：`src/agent/react_agent.py`
- 测试：`tests/test_react_agent.py`

- [ ] **步骤 1：编写测试**

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.agent.react_agent import run_react_agent
from src.models.schemas import KnowledgeSummary


@pytest.mark.asyncio
async def test_react_agent_returns_knowledge_summary():
    """ReAct agent 应搜索 → 阅读 → 总结 并返回 KnowledgeSummary"""
    with patch("src.agent.react_agent.web_search") as mock_search:
        mock_search.return_value = [
            {"title": "RAG 介绍", "url": "https://example.com", "content": "RAG 是..."}
        ]
        with patch("src.agent.react_agent.fetch_content") as mock_fetch:
            mock_fetch.return_value.content = "RAG 即检索增强生成，结合了检索和 LLM 生成能力"
            with patch("langchain_anthropic.ChatAnthropic", autospec=True) as MockLLM:
                mock_msg = AsyncMock()
                mock_msg.content = """{
                    "topic": "RAG",
                    "core_concepts": ["检索增强生成", "向量数据库", "Embedding"],
                    "learning_points": ["先理解 Embedding", "再学向量检索", "最后了解 RAG pipeline"],
                    "related_techs": ["LangChain", "LlamaIndex"]
                }"""
                MockLLM.return_value.ainvoke = AsyncMock(return_value=mock_msg)
                result = await run_react_agent("什么是 RAG")
                assert result.topic == "RAG"
                assert len(result.core_concepts) == 3
                assert mock_search.called


@pytest.mark.asyncio
async def test_react_agent_empty_search():
    """搜索结果为空时返回错误提示"""
    with patch("src.agent.react_agent.web_search") as mock_search:
        mock_search.return_value = []
        with patch("langchain_anthropic.ChatAnthropic", autospec=True) as MockLLM:
            mock_msg = AsyncMock()
            mock_msg.content = """{"topic": "", "core_concepts": [], "learning_points": [], "related_techs": []}"""
            MockLLM.return_value.ainvoke = AsyncMock(return_value=mock_msg)
            result = await run_react_agent("xxx罕见技术xxx")
            assert result.topic == ""
            assert result.core_concepts == []
```

- [ ] **步骤 2：运行测试确认失败**

运行：`pytest tests/test_react_agent.py -v`
预期：FAIL

- [ ] **步骤 3：编写 react_agent.py**

```python
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import settings
from src.models.schemas import KnowledgeSummary
from src.tools.web_search import web_search
from src.tools.content_fetch import fetch_content
from src.logging_config import setup_logging

logger = setup_logging()

SUMMARIZE_PROMPT = """你是一个技术学习助手。根据以下搜索资料，为用户总结技术知识点。

要求：
1. 提炼核心概念（core_concepts）
2. 列出学习要点（learning_points），按入门到深入排列
3. 列出相关技术（related_techs）

只返回 JSON：
{"topic": "技术名", "core_concepts": [...], "learning_points": [...], "related_techs": [...]}"""


async def run_react_agent(query: str) -> KnowledgeSummary:
    """ReAct 循环：搜索 → 阅读最佳结果 → LLM 提炼总结"""
    logger.info("ReAct agent 启动", query=query[:100])

    # Step 1: Search
    search_results = await web_search(query)
    logger.debug("ReAct 搜索完成", count=len(search_results))

    # Step 2: Read（取前 2 个结果的内容）
    contents = []
    for r in search_results[:2]:
        fetched = await fetch_content(r["url"])
        if fetched.content:
            contents.append(fetched.content[:5000])
    combined_content = "\n\n---\n\n".join(contents)

    # Step 3: Summarize
    try:
        llm = ChatAnthropic(
            model=settings.anthropic_model_simple,
            api_key=settings.anthropic_api_key,
            max_tokens=1000,
        )
        msgs = [
            SystemMessage(content=SUMMARIZE_PROMPT),
            HumanMessage(content=f"用户查询：{query}\n\n搜索资料：{combined_content[:8000] or '未找到相关资料'}"),
        ]
        response = await llm.ainvoke(msgs)
        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content)
        return KnowledgeSummary(**data)
    except Exception as e:
        logger.error("ReAct 总结失败", error=str(e))
        return KnowledgeSummary(topic=query, learning_points=["总结失败，请重试"])
```

- [ ] **步骤 4：运行测试确认通过**

运行：`pytest tests/test_react_agent.py -v`
预期：PASS（2 passed）

- [ ] **步骤 5：提交**

```bash
git add src/agent/react_agent.py tests/test_react_agent.py
git commit -m "添加 ReAct Agent：搜索→阅读→总结 学习知识闭环"
```

---

### 任务 11：创建 FastAPI + CLI 入口

**文件：**
- 创建：`src/main.py`

- [ ] **步骤 1：编写 main.py**

```python
import asyncio
import sys
from fastapi import FastAPI
from src.config import settings
from src.logging_config import setup_logging
from src.models.schemas import UserInput
from src.router.router import route_task
from src.agent.react_agent import run_react_agent
from src.models.schemas import TaskType

logger = setup_logging()
app = FastAPI(title="LearnAgent", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/learn")
async def learn(user_input: UserInput):
    """学习接口：输入技术名，返回知识总结"""
    logger.info("API learn 请求", query=user_input.query[:50])
    decision = await route_task(user_input)
    if decision.task_type == TaskType.COMPLEX:
        return {"task_type": "complex", "message": "复杂任务支持将在 P1 阶段实现", "reason": decision.reason}
    result = await run_react_agent(user_input.query)
    return {"task_type": "simple", "result": result.model_dump()}


async def cli_main():
    """CLI 入口"""
    logger.info("LearnAgent CLI 启动")
    print("=" * 50)
    print("LearnAgent - AI 学习助手")
    print("输入 '/quit' 退出，输入技术名开始学习")
    print("=" * 50)

    while True:
        try:
            query = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query:
            continue
        if query == "/quit":
            break

        decision = await route_task(UserInput(query=query))
        print(f"[路由] {decision.task_type.value} — {decision.reason}")

        if decision.task_type == TaskType.COMPLEX:
            print("(复杂任务将在 P1 阶段支持)")
            continue

        result = await run_react_agent(query)
        print(f"\n📖 {result.topic}")
        print(f"核心概念: {', '.join(result.core_concepts) if result.core_concepts else '无'}")
        print(f"学习要点:")
        for i, point in enumerate(result.learning_points, 1):
            print(f"  {i}. {point}")
        print(f"相关技术: {', '.join(result.related_techs) if result.related_techs else '无'}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        asyncio.run(cli_main())
```

- [ ] **步骤 2：验证代码可导入**

运行：`python -c "from src.main import app; print('FastAPI app 创建成功')"`

- [ ] **步骤 3：提交**

```bash
git add src/main.py
git commit -m "添加 FastAPI + CLI 入口：/learn 接口和交互式命令行"
```

---

### 任务 12：P0 集成测试和验证

- [ ] **步骤 1：编写集成测试 — tests/test_integration.py**

```python
import pytest
from src.main import app
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_learn_endpoint_simple_task():
    """模拟简单任务全链路"""
    with patch("langchain_anthropic.ChatAnthropic", autospec=True) as MockLLM:
        mock_msg = AsyncMock()
        mock_msg.content = '{"task_type": "simple", "reason": "查询概念"}'

        mock_summary_msg = AsyncMock()
        mock_summary_msg.content = '{"topic": "RAG", "core_concepts": ["检索", "增强"], "learning_points": ["第一步"], "related_techs": []}'

        llm_instance = MockLLM.return_value
        llm_instance.ainvoke = AsyncMock(side_effect=[mock_msg, mock_summary_msg])

        with patch("src.agent.react_agent.web_search") as mock_search:
            mock_search.return_value = [{"title": "t", "url": "http://x.com", "content": "c"}]
            with patch("src.agent.react_agent.fetch_content") as mock_fetch:
                mock_fetch.return_value.content = "content"
                resp = client.post("/learn", json={"query": "什么是 RAG"})
                assert resp.status_code == 200
                data = resp.json()
                assert data["task_type"] == "simple"
                assert data["result"]["topic"] == "RAG"
```

- [ ] **步骤 2：运行集成测试**

运行：`pytest tests/test_integration.py -v`
预期：PASS

- [ ] **步骤 3：运行全部测试**

运行：`pytest -v`
预期：所有测试通过

- [ ] **步骤 4：提交**

```bash
git add tests/test_integration.py
git commit -m "添加 P0 集成测试：健康检查 + 学习接口全链路 Mock 验证"
```

---

## 阶段三：P1 — 场景化教学项目生成

### 任务 13：实现 Filesystem 工具

**文件：**
- 创建：`src/tools/filesystem.py`
- 测试：`tests/test_tools/test_filesystem.py`

- [ ] **步骤 1：编写测试**

```python
import os
import pytest
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
```

- [ ] **步骤 2：运行测试确认失败**

- [ ] **步骤 3：编写 filesystem.py**

```python
import os
from src.logging_config import setup_logging

logger = setup_logging()


def create_project(base_dir: str, project_name: str) -> str:
    """在 base_dir 下创建项目目录，含 README.md"""
    project_path = os.path.join(base_dir, project_name)
    os.makedirs(project_path, exist_ok=True)
    readme = os.path.join(project_path, "README.md")
    with open(readme, "w", encoding="utf-8") as f:
        f.write(f"# {project_name}\n\nLearnAgent 教学项目\n")
    logger.info("create_project", path=project_path)
    return project_path


def write_file(project_path: str, filename: str, content: str) -> str:
    """在项目目录下写文件"""
    file_path = os.path.join(project_path, filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("write_file", path=file_path, size=len(content))
    return file_path
```

- [ ] **步骤 4：运行测试确认通过**

- [ ] **步骤 5：提交**

```bash
git add src/tools/filesystem.py tests/test_tools/test_filesystem.py
git commit -m "添加 Filesystem 工具：项目目录创建 + 文件写入"
```

---

### 任务 14：实现 Plan-then-Execute Agent（LangGraph 图式）

**文件：**
- 创建：`src/agent/plan_execute_agent.py`
- 测试：`tests/test_plan_execute_agent.py`

- [ ] **步骤 1：编写测试**

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.agent.plan_execute_agent import build_plan_execute_graph


def test_graph_builds_successfully():
    """LangGraph 图应成功编译"""
    graph = build_plan_execute_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_graph_plan_node():
    """plan 节点应生成教学计划"""
    graph = build_plan_execute_graph()
    with patch("langchain_anthropic.ChatAnthropic", autospec=True) as MockLLM:
        mock_msg = AsyncMock()
        mock_msg.content = """{"steps": [
            {"title": "安装 Redis", "description": "使用 Docker 安装", "files": {"docker-compose.yml": "..."}},
            {"title": "基础读写", "description": "SET/GET 操作", "files": {"main.py": "import redis\\nr = redis.Redis()\\nr.set('k', 'v')"}},
            {"title": "发布订阅", "description": "Pub/Sub 模式", "files": {"publisher.py": "...", "subscriber.py": "..."}}
        ]}"""
        MockLLM.return_value.ainvoke = AsyncMock(return_value=mock_msg)
        from src.agent.plan_execute_agent import plan_node
        from src.memory.working import create_initial_state
        state = create_initial_state("我要学 Redis")
        result = await plan_node(state)
        assert "plan" in result
        assert len(result["plan"]["steps"]) == 3
```

- [ ] **步骤 2：运行测试确认失败**

- [ ] **步骤 3：编写 plan_execute_agent.py**

```python
import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import settings
from src.memory.working import AgentState
from src.tools.filesystem import create_project, write_file
from src.logging_config import setup_logging

logger = setup_logging()

PLAN_PROMPT = """你是技术教学专家。为用户要学的技术设计渐进式教学场景。

规则：
- 3-5 个步骤，从易到难
- 每一步包含：场景描述、要创建的文件及完整代码
- 代码可以是 Python/JS/YAML 等，确保可以直接运行

返回 JSON：
{
  "steps": [
    {
      "title": "场景名",
      "description": "本步骤学什么",
      "files": {"文件名": "文件完整内容"}
    }
  ]
}"""


async def plan_node(state: AgentState) -> dict:
    """制定教学计划"""
    logger.info("plan_node 开始", query=state["user_query"][:50])
    llm = ChatAnthropic(
        model=settings.anthropic_model_complex,
        api_key=settings.anthropic_api_key,
        max_tokens=4000,
    )
    msgs = [
        SystemMessage(content=PLAN_PROMPT),
        HumanMessage(content=f"用户要学：{state['user_query']}"),
    ]
    response = await llm.ainvoke(msgs)
    content = response.content.strip()
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    plan = json.loads(content)
    logger.info("plan_node 完成", step_count=len(plan["steps"]))
    return {
        "plan": plan,
        "messages": [{"role": "assistant", "content": f"制定了 {len(plan['steps'])} 步学习计划"}],
    }


async def execute_node(state: AgentState) -> dict:
    """执行当前教学步骤：创建文件"""
    plan = state.get("plan", {})
    steps = plan.get("steps", [])
    current_step = state.get("current_step", 0)

    if current_step >= len(steps):
        return {"messages": [{"role": "assistant", "content": "所有步骤已完成！"}]}

    step = steps[current_step]
    project_dir = state.get("project_dir", f"./projects/{state['user_query'].replace(' ', '-')}")

    logger.info("execute_node", step=current_step + 1, title=step["title"])

    # 首次执行时创建项目目录
    if current_step == 0:
        import os
        base = os.path.expanduser("~/LearnAgent/projects")
        create_project(base, state["user_query"].replace(" ", "-"))

    step_result = {"step": current_step + 1, "title": step["title"], "description": step["description"], "files": []}
    for filename, content in step.get("files", {}).items():
        file_path = write_file(project_dir, filename, content)
        step_result["files"].append(file_path)

    return {
        "current_step": current_step + 1,
        "messages": [{"role": "assistant", "content": json.dumps(step_result, ensure_ascii=False)}],
        "project_dir": project_dir,
    }


async def summarize_node(state: AgentState) -> dict:
    """教学完成后的总结"""
    plan = state.get("plan", {})
    return {
        "messages": [{"role": "assistant", "content": "教学项目已全部完成！你可以运行项目查看效果。"}],
    }


def should_continue(state: AgentState) -> str:
    """判断是否还有步骤待执行"""
    plan = state.get("plan", {})
    total = len(plan.get("steps", []))
    current = state.get("current_step", 0)
    return "summarize" if current >= total else "execute"


def build_plan_execute_graph():
    """构建 Plan-then-Execute 的 LangGraph 图"""
    from langgraph.graph import StateGraph, END
    builder = StateGraph(AgentState)
    builder.add_node("plan", plan_node)
    builder.add_node("execute", execute_node)
    builder.add_node("summarize", summarize_node)
    builder.set_entry_point("plan")
    builder.add_edge("plan", "execute")
    builder.add_conditional_edges("execute", should_continue, {"execute": "execute", "summarize": "summarize"})
    builder.add_edge("summarize", END)
    return builder.compile(checkpointer=MemorySaver())
```

- [ ] **步骤 4：运行测试确认通过**

- [ ] **步骤 5：提交**

```bash
git add src/agent/plan_execute_agent.py tests/test_plan_execute_agent.py
git commit -m "添加 Plan-then-Execute Agent：LangGraph 图式教学项目生成"
```

---

### 任务 15：更新 main.py 接入复杂任务路径

**文件：**
- 修改：`src/main.py`

- [ ] **步骤 1：修改 main.py 的 learn 接口和 CLI**

修改 `/learn` 接口和 CLI 中的复杂任务分支，使其调用 `plan_execute_agent`：

找到 `if decision.task_type == TaskType.COMPLEX:` 这两处，替换为：

```python
if decision.task_type == TaskType.COMPLEX:
    from src.agent.plan_execute_agent import build_plan_execute_graph
    from src.memory.working import create_initial_state
    graph = build_plan_execute_graph()
    state = create_initial_state(user_input.query)
    config = {"configurable": {"thread_id": "learn-session"}}

    async for event in graph.astream(state, config):
        for _, node_output in event.items():
            msgs = node_output.get("messages", [])
            for m in msgs:
                print(f"\n{m['content']}")
    continue  # /learn 接口中则 return
```

- [ ] **步骤 2：验证代码可导入**

运行：`python -c "from src.main import app; print('OK')"`

- [ ] **步骤 3：提交**

```bash
git add src/main.py
git commit -m "主入口接入 Plan-then-Execute Agent，复杂任务使用 LangGraph 图式执行"
```

---

### 任务 16：实现短期记忆（SQLite + ChromaDB）

**文件：**
- 创建：`src/memory/short_term.py`
- 测试：`tests/test_memory/test_short_term.py`

- [ ] **步骤 1：编写测试**

```python
import pytest
from src.memory.short_term import ShortTermMemory


@pytest.fixture
async def memory(tmp_path):
    db_path = str(tmp_path / "test.db")
    stm = ShortTermMemory(db_path)
    await stm.initialize()
    yield stm


@pytest.mark.asyncio
async def test_save_and_search(memory):
    await memory.save("RAG 是检索增强生成技术")
    await memory.save("LangGraph 是 agent 编排框架")
    results = await memory.search("什么是 RAG")
    assert len(results) > 0
    assert any("RAG" in r for r in results)


@pytest.mark.asyncio
async def test_list_recent(memory):
    await memory.save("条目 1")
    await memory.save("条目 2")
    recents = await memory.list_recent(limit=2)
    assert len(recents) == 2
```

- [ ] **步骤 2：运行测试确认失败**

- [ ] **步骤 3：编写 short_term.py**

```python
import aiosqlite
from chromadb import PersistentClient
from src.logging_config import setup_logging

logger = setup_logging()


class ShortTermMemory:
    def __init__(self, sqlite_path: str = "data/memory.db", chroma_path: str = "data/chroma"):
        self.sqlite_path = sqlite_path
        self.chroma_path = chroma_path
        self.db = None
        self.chroma = None
        self.collection = None

    async def initialize(self):
        import os
        os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
        self.db = await aiosqlite.connect(self.sqlite_path)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.db.commit()
        self.chroma = PersistentClient(path=self.chroma_path)
        try:
            self.collection = self.chroma.get_or_create_collection("learnagent_memory")
        except Exception:
            self.collection = self.chroma.create_collection("learnagent_memory")
        logger.info("ShortTermMemory 初始化完成")

    async def save(self, content: str):
        # SQLite
        await self.db.execute("INSERT INTO memories (content) VALUES (?)", (content,))
        await self.db.commit()
        # ChromaDB（用原文做简单向量存储，生产环境应使用 embedding 模型）
        import uuid
        self.collection.add(documents=[content], ids=[str(uuid.uuid4())])
        logger.debug("memory saved", length=len(content))

    async def search(self, query: str, limit: int = 3) -> list[str]:
        try:
            results = self.collection.query(query_texts=[query], n_results=limit)
            docs = results.get("documents", [[]])[0]
            return docs
        except Exception:
            return []

    async def list_recent(self, limit: int = 10) -> list[str]:
        cursor = await self.db.execute(
            "SELECT content FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]
```

- [ ] **步骤 4：运行测试确认通过**

- [ ] **步骤 5：提交**

```bash
git add src/memory/short_term.py tests/test_memory/test_short_term.py
git commit -m "添加短期记忆：SQLite 结构化存储 + ChromaDB 语义检索"
```

---

### 任务 17：实现用户画像（JSON 文件）

**文件：**
- 创建：`src/memory/user_profile.py`
- 测试：`tests/test_memory/test_user_profile.py`

- [ ] **步骤 1：编写测试**

```python
import json
from src.memory.user_profile import UserProfile, load_profile, save_profile


def test_load_profile_creates_default(tmp_path):
    path = str(tmp_path / "profile.json")
    profile = load_profile(path)
    assert profile.skills_known == []
    assert profile.skills_learning == []


def test_save_and_load_profile(tmp_path):
    path = str(tmp_path / "profile.json")
    profile = load_profile(path)
    profile.skills_known.append("Python")
    profile.preferred_difficulty = "intermediate"
    save_profile(profile, path)
    with open(path) as f:
        data = json.load(f)
    assert "Python" in data["skills_known"]
    assert data["preferred_difficulty"] == "intermediate"
```

- [ ] **步骤 2：运行测试确认失败**

- [ ] **步骤 3：编写 user_profile.py**

```python
import json
import os
from pydantic import BaseModel
from typing import Optional
from src.logging_config import setup_logging

logger = setup_logging()


class UserProfile(BaseModel):
    skills_known: list[str] = []
    skills_learning: list[str] = []
    preferred_difficulty: str = "beginner"
    preferred_language: str = "python"
    learning_goals: list[str] = []


def load_profile(path: str = "data/profile.json") -> UserProfile:
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        profile = UserProfile()
        save_profile(profile, path)
        logger.info("创建新用户画像", path=path)
        return profile
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return UserProfile(**data)


def save_profile(profile: UserProfile, path: str = "data/profile.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(), f, ensure_ascii=False, indent=2)
    logger.debug("用户画像已保存", path=path)
```

- [ ] **步骤 4：运行测试确认通过**

- [ ] **步骤 5：提交**

```bash
git add src/memory/user_profile.py tests/test_memory/test_user_profile.py
git commit -m "添加用户画像：JSON 持久化，记录已知技能和学习偏好"
```

---

## 阶段四：P2 — 定时推送

### 任务 18：实现 Notify 工具（Cron + Slack）

**文件：**
- 创建：`src/tools/notify.py`
- 测试：`tests/test_tools/test_notify.py`

- [ ] **步骤 1：编写测试**

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.tools.notify import send_slack_message, start_scheduler


@pytest.mark.asyncio
async def test_send_slack_message():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = lambda: None
        result = await send_slack_message("测试消息")
        assert result is True


@pytest.mark.asyncio
async def test_send_slack_message_no_webhook():
    with patch("src.tools.notify.settings") as mock_settings:
        mock_settings.slack_webhook_url = ""
        result = await send_slack_message("测试")
        assert result is False
```

- [ ] **步骤 2：运行测试确认失败**

- [ ] **步骤 3：编写 notify.py**

```python
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.config import settings
from src.logging_config import setup_logging

logger = setup_logging()

scheduler = AsyncIOScheduler()


async def send_slack_message(text: str) -> bool:
    """通过 Slack Webhook 发送消息"""
    if not settings.slack_webhook_url:
        logger.warning("Slack Webhook 未配置")
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                settings.slack_webhook_url,
                json={"text": text},
            )
            resp.raise_for_status()
            logger.info("Slack 消息已发送", text=text[:50])
            return True
    except Exception as e:
        logger.error("Slack 发送失败", error=str(e))
        return False


async def daily_push_callback():
    """每日定时推送：搜索 AI Agent 最新动态并发送"""
    from src.tools.web_search import web_search
    logger.info("定时推送触发")
    results = await web_search("AI Agent 最新进展 2026", max_results=3)
    if not results:
        await send_slack_message("📚 今日 AI Agent 学习推荐：暂无新内容")
        return
    lines = ["📚 今日 AI Agent 学习推荐："]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. *{r['title']}* — {r['url']}")
        lines.append(f"   {r['content'][:120]}...")
    await send_slack_message("\n".join(lines))


def start_scheduler(hour: int = 9, minute: int = 0):
    """启动定时调度器：每天 9 点推送"""
    from apscheduler.triggers.cron import CronTrigger
    scheduler.add_job(
        daily_push_callback,
        CronTrigger(hour=hour, minute=minute),
        id="daily_push",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("定时调度器已启动", time=f"{hour:02d}:{minute:02d}")
```

- [ ] **步骤 4：运行测试确认通过**

- [ ] **步骤 5：提交**

```bash
git add src/tools/notify.py tests/test_tools/test_notify.py
git commit -m "添加 Notify 工具：Slack Webhook + APScheduler 定时推送"
```

---

### 任务 19：更新 main.py 集成定时推送

**文件：**
- 修改：`src/main.py`

- [ ] **步骤 1：在启动时初始化调度器**

在 `app = FastAPI(...)` 之后添加：

```python
@app.on_event("startup")
async def startup():
    from src.tools.notify import start_scheduler
    start_scheduler()
    logger.info("LearnAgent 启动完成")
```

在 CLI 入口的启动逻辑中（`__main__` 块），服务器模式也初始化调度器：

```python
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        import uvicorn
        from src.tools.notify import start_scheduler
        start_scheduler()
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        asyncio.run(cli_main())
```

- [ ] **步骤 2：验证**

运行：`python -c "from src.main import app; print('OK')"`

- [ ] **步骤 3：提交**

```bash
git add src/main.py
git commit -m "启动时初始化定时推送调度器"
```

---

## 阶段五：收尾

### 任务 20：运行全部测试 + Lint

- [ ] **步骤 1：安装依赖**

```bash
pip install -e ".[dev]"
```

- [ ] **步骤 2：运行 lint**

```bash
ruff check src/ tests/
```

预期：无错误

- [ ] **步骤 3：运行全部测试**

```bash
pytest -v
```

预期：所有测试通过

- [ ] **步骤 4：如有 lint 问题或测试失败，修复后重新验证**

- [ ] **步骤 5：提交**

```bash
git add -A
git commit -m "项目收尾：依赖安装验证 + lint + 全量测试通过"
```
