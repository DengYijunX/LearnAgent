# LearnAgent Codex 从零构建实验

LearnAgent 是一个学习型 Agent 实验项目，目标是帮助自学者完成「发现主题、理解核心概念、阅读资料或仓库、动手实践、复盘进度」的学习闭环。

当前分支采用 Python CLI first 的构建方式。第一阶段重点是项目结构、配置管理、LLM 抽象、工具注册、Router、Workflow、本地 Memory / Session 存储和基础测试。

## 第一阶段方向

- 优先实现 CLI，不引入 FastAPI 或前端。
- DeepSeek 是第一阶段主要真实 LLM 服务商，通过 OpenAI-compatible API 接入。
- 单元测试默认使用 mock client 和 mock tool。
- 真实 LLM 检查通过 smoke script 和环境变量隔离。
- 第一阶段 Web Search 使用 mock 实现；GitHub 分析只读取公开 README，不接 GitHub API 或 token。
- 本地 session、run trace、memory 和 learning todo 数据存放在 `storage/` 下，并由 Git 忽略。

## 配置

运行真实 LLM smoke test 前，可以基于 `.env.example` 创建本地 `.env`。当前配置模块会读取项目根目录下的 `.env`，并且环境变量优先级高于 `.env`。不要提交 `.env`。

```env
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=
DEEPSEEK_SMALL_MODEL=
DEEPSEEK_LARGE_MODEL=
LEARNAGENT_MODEL_MODE=normal
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=2048
RUN_REAL_TESTS=0
```

DeepSeek 的实际 model ID 必须来自服务商配置，不应硬编码在 workflow、agent loop 或 tool 代码中。

## 可用命令

运行 mock 模式 CLI：

```powershell
python -m app.main
python -m app.main "我想学习 LangGraph"
python -m app.main --json "我想学习 LangGraph"
```

运行真实 DeepSeek CLI：

```powershell
python -m app.main --real --mode normal "我想学习 LangGraph"
python -m app.main --real --json --mode normal "我想学习 LangGraph"
```

运行单元测试：

```powershell
python -m pytest
```

手动验证真实 DeepSeek API：

```powershell
python scripts/smoke_llm_real.py
```

手动验证真实网页读取：

```powershell
python scripts/smoke_read_url_real.py https://example.com/
```

手动验证公开 GitHub README 分析：

```powershell
python scripts/smoke_github_repo_real.py https://github.com/pallets/flask
```

手动验证真实 DeepSeek LLM + mock tools 的最小 Agent 闭环：

```powershell
python scripts/smoke_agent_real.py
```

真实集成测试和 smoke script 只有在 `RUN_REAL_TESTS=1` 且必要 API key 已配置时，才应调用外部服务。
