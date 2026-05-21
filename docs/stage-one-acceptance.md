# 第一阶段验收说明

日期：2026-05-21

分支：`agent/codex-rebuild`

## 阶段结论

LearnAgent 第一阶段 MVP 已完成并推送到远端分支。当前版本可以通过 Python CLI 跑通最小学习 Agent 闭环，支持 mock LLM 的稳定本地测试，也支持 DeepSeek OpenAI-compatible API 的真实 smoke 验证。

第一阶段重点不是完整产品体验，而是把核心运行时边界搭起来：配置、LLM 抽象、模型选择、Router、Tool Registry、Agent Loop、Workflow、本地 Session / Memory、基础工具和测试体系。

## 已实现能力

- CLI 入口：`python -m app.main`
- 配置管理：`.env` + `app/config/settings.py`
- LLM 抽象：`LLMClient` 接口
- LLM 实现：`MockLLMClient`、`DeepSeekLLMClient`
- 模型选择：简单规则型 `ModelSelector`
- Router：规则匹配用户输入意图
- Agent Loop：支持标准 tool calling 和 JSON action fallback
- Tool Layer：`Tool` 基类与 `ToolRegistry`
- Web Search：第一阶段 mock search
- URL 读取：真实 `ReadUrlTool`
- GitHub 仓库分析：公开 README 读取，不接 GitHub API，不使用 token
- Workflow：串联 Router、Agent Loop、Tool Registry、Session 和 Memory
- SessionStore：JSONL 本地追加记录
- MemoryStore：Markdown + frontmatter
- Learning Todo：本地 JSON 存储与 `learning_todo_write` 工具
- 输出结构：`LearningOutput`
- CLI JSON 输出：`--json`
- 测试：pytest 基础单元测试和 smoke script

## 第一阶段运行方式

mock 模式：

```powershell
python -m app.main "我想学习 LangGraph"
```

JSON 输出：

```powershell
python -m app.main --json "我想学习 LangGraph"
```

真实 DeepSeek CLI：

```powershell
python -m app.main --real --mode normal "我想学习 LangGraph"
```

GitHub URL 路由验收：

```powershell
python -m app.main --json "https://github.com/pallets/flask 这个项目怎么学"
```

## 真实 smoke 验证

真实 LLM smoke：

```powershell
$env:RUN_REAL_TESTS='1'
python scripts\smoke_llm_real.py
```

真实 LLM + mock tools Agent 小闭环：

```powershell
$env:RUN_REAL_TESTS='1'
python scripts\smoke_agent_real.py
```

真实网页读取：

```powershell
$env:RUN_REAL_TESTS='1'
python scripts\smoke_read_url_real.py https://example.com/
```

公开 GitHub README 分析：

```powershell
$env:RUN_REAL_TESTS='1'
python scripts\smoke_github_repo_real.py https://github.com/pallets/flask
```

## 最近验收记录

- `python -m pytest -q`：72 passed
- `python -m compileall -q app scripts`：通过
- mock CLI：通过
- JSON CLI：通过
- GitHub URL JSON 路由：通过，识别为 `analyze_repo`
- 公开 GitHub README smoke：通过
- DeepSeek LLM smoke：通过
- DeepSeek Agent smoke：首次出现 TLS 瞬时断连，重试后通过

## 本地数据与安全边界

- `.env` 不提交
- `storage/` 不提交
- `logs/` 不提交
- API key 不写入代码、不写入日志
- 用户学习记录、session trace、LLM 原始响应只保存在本地
- 单元测试默认不访问网络、不消耗 API
- 真实 smoke 只有设置 `RUN_REAL_TESTS=1` 后才调用外部服务

## 第一阶段明确不做

- 不引入 FastAPI / Flask / 前端
- 不接真实 Web Search API
- 不接 GitHub API
- 不访问私有 GitHub 仓库
- 不引入数据库、队列、RAG、MCP、Sandbox
- 不做复杂多 Agent 架构
- 不做复杂多模型智能调度

## 已知限制

- mock LLM 默认不会主动调用工具，所以 CLI mock 模式主要用于验证路由、workflow 和输出结构。
- `github_repo_analyzer` 只尝试读取 main/master 分支的 `README.md`。
- `ReadUrlTool` 只做轻量 HTML 可见文本提取，不做复杂网页清洗。
- Agent Loop 第一阶段只稳定支持一轮工具调用后生成最终回答。
- DeepSeek 真实 smoke 依赖外部服务状态，可能遇到 503 或瞬时网络断连。

## 下一阶段建议

优先级建议如下：

1. 增强 URL 内容清洗和 token 长度控制。
2. 接入真实 Web Search，并单独测试搜索质量、异常处理和结果清洗。
3. 扩展 GitHub 仓库分析到目录结构和依赖文件，但仍不默认引入 token。
4. 为真实 Agent Loop 增加更细的工具调用预算、重复调用保护和错误恢复。
5. 在 CLI 稳定后，再考虑 FastAPI 或前端入口。
