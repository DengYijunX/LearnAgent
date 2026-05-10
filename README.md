# LearnAgent

AI 学习助手 — 发现新技术 → 理解核心概念 → 动手实践，一个完整的学
习闭环。

## 快速开始

```bash
# 安装
pip install -e ".[dev]"

# 配置
cp .env.example .env
# 编辑 .env，填入 API Key

# 运行 CLI
python -m src.main

# 或启动 API 服务
python -m src.main server
```

## 配置切换 LLM

在 `.env` 中设置 `LLM_PROVIDER`，支持三个 provider：

```env
# DeepSeek（当前默认）
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxx

# Anthropic
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-xxx

# OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-xxx
```

Provider 特有配置会自动加载（如 DeepSeek 的 `base_url`），也可手动覆盖 `LLM_BASE_URL` 和 `LLM_MODEL_SIMPLE` / `LLM_MODEL_COMPLEX`。

## 使用方式

### CLI 交互模式

```
> 什么是RAG
[路由] simple — 概念查询
📖 RAG (Retrieval-Augmented Generation)
核心概念: 检索增强生成, 向量数据库, Embedding
学习要点:
  1. 先理解 Embedding
  2. 再学向量检索
  3. 最后了解 RAG pipeline
相关技术: LangChain, LlamaIndex

> 我要学 FastAPI
[路由] complex — 教学项目生成
制定了 4 步学习计划
...
```

### API

```bash
curl -X POST http://localhost:8000/learn \
  -H "Content-Type: application/json" \
  -d '{"query":"什么是向量数据库"}'
```

## 架构

```
用户输入 → Router（LLM 分类）
              ├─ simple → ReAct Agent（搜索→抓取→总结）
              └─ complex → Plan-Execute Agent（LangGraph 编排）
                             ├─ plan：LLM 生成教学计划
                             └─ execute：逐步创建代码文件
```

```
agent/
├── src/
│   ├── main.py                  # FastAPI + CLI 入口
│   ├── config.py                # 环境变量配置
│   ├── llm.py                   # LLM 工厂（多 provider 切换）
│   ├── logging_config.py        # structlog 初始化
│   ├── router/router.py         # LLM 任务分类
│   ├── agent/
│   │   ├── react_agent.py       # 简单任务 ReAct 循环
│   │   └── plan_execute_agent.py # 复杂任务 Plan-then-Execute
│   ├── tools/
│   │   ├── web_search.py        # Tavily 搜索
│   │   ├── content_fetch.py     # Jina AI Reader + httpx 降级
│   │   ├── github_disco.py      # GitHub Trending + 搜索
│   │   ├── filesystem.py        # 本地项目文件创建
│   │   └── notify.py            # Slack Webhook + 定时推送
│   ├── memory/
│   │   ├── working.py           # LangGraph State 工作记忆
│   │   ├── short_term.py        # SQLite + ChromaDB
│   │   └── user_profile.py      # JSON 用户画像
│   └── models/schemas.py        # Pydantic 数据模型
└── tests/                       # 33 个测试
```

## 命令

```bash
make install          # 安装依赖
make run              # 启动 CLI
make test             # 运行单元测试
make test-integration # 运行集成测试（需要 API Key）
make lint             # 代码检查
make clean            # 清理缓存
```

## 依赖

- **框架**: FastAPI, LangGraph, LangChain
- **LLM**: langchain-anthropic, langchain-openai
- **工具**: Tavily, httpx, ChromaDB
- **存储**: aiosqlite, ChromaDB
- **日志**: structlog
- **调度**: APScheduler
- **测试**: pytest, pytest-asyncio, ruff

## License

MIT
