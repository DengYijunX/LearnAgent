# LearnAgent v1.1 — 记忆层 + 控制面 + Prompt Registry

## 架构总览

```
                       ┌──────────────────────────────┐
                       │      Registry (控制面)         │
                       │   模块注册 | 权限 | 配置校验   │
                       │   CLI /status                 │
                       └──────────────────────────────┘
                                    │
    ┌──────┬─────────┬─────────┬────┴────┬──────────┬─────────┐
    ▼      ▼         ▼         ▼         ▼          ▼         ▼
┌──────┐┌──────┐┌─────────┐┌──────┐┌──────────┐┌──────┐┌────────┐
│ 核心 ││ 记忆 ││Artifact ││ 工具 ││  会话日志 ││ 评估 ││ 权限   │
│Router││Layer ││(用户面) ││search││sessions  ││Eval  ││校验   │
│ReAct │└──────┘└─────────┘│fetch ││.jsonl    ││框架  │└────────┘
│Plan  │                  │github│└──────────┘└──────┘
│LLM   │                  │fs    │
│Prompt│                  │writer│
│Reg   │                  │      │
└──────┘                  └──────┘
```

**v1.1 不做：** FAISS 知识库、Skills、Plugins、SQLite、动态 `/toggle`

---

## 实现约束（防止跑偏）

### 核心原则
> **学习 > 记忆**：记忆/产物写入失败不能阻塞核心学习流程。记不住也要能学。

1. **skills_known 不自动升级** — simple 概念学习后只加入 `skills_learning` + `recent_topics`；完成项目或多次学习后才升级到 `skills_known`
2. **search_memory 返回摘要** — 默认最多 3-5 条，只返回 topic / path / type / tags / created_at，不读完整 md 正文。需要详情时再按 path 读取
3. **MEMORY.md 全量重渲染** — 每次由 index.json `render_memory_md()` 重新生成（header → profile → recent_topics → 最近 20 条 learnings → artifacts），不做原地截断
4. **Prompt Registry 极简** — 第一版只做 `load_prompt(name: str) -> str`，文件放 `src/core/prompts/{router,summarize,plan_execute}.md`，不做版本号、热更新、模板继承
5. **path_safety 防穿越** — `base = Path(base_dir).resolve(); target = (base / relative_path).resolve(); target.relative_to(base)`，防止 `../`、绝对路径、软链接跳出
6. **secret redaction 两层规则** — 字段名命中（api_key/apikey/token/secret/authorization/password）→ 直接替换；值命中密钥模式（`sk-...`/`Bearer ...`/`ghp_...`）→ 替换；不误删普通文本
7. **artifact 文件名带日期** — `artifacts/summaries/2026-05-10-rag-summary.md`，避免多次学习同一主题时覆盖
8. **日志用相对路径** — sessions 和 plan_execute_complete 中的路径尽量用相对路径，内部执行可用绝对路径
9. **config validator 默认只 warning** — `strict=False` 只 warning，`strict=True` 才抛异常；测试环境不因缺少 Key 而启动失败
10. **新测试用 tmp_path** — 不依赖真实 API Key；所有 memory / artifact / registry 测试使用 tmp_path；短命模块 deprecated 仅在类初始化时 warn 一次

---

## 设计原则

### 数据权威性
- `index.json` 是 **唯一 source of truth**（机器索引），MEMORY.md 由 index.json **单向渲染**
- `profile.json` 是结构数据权威，不做 markdown 同步

### 文件格式矩阵

| 文件 | 格式 | 谁读 | 作用 | 写入方式 |
|------|------|------|------|----------|
| index.json | JSON | 程序 | 记忆索引，source of truth | atomic write |
| MEMORY.md | Markdown | 人 + Agent | 启动时加载，由 index.json 渲染 | atomic write |
| profile.json | JSON | 程序 | 用户画像 | atomic write |
| learnings/*.md | Markdown + YAML fm | 人 + Agent | 单次学习记录 | atomic write |
| sessions/*.jsonl | JSONL | 程序 | Agent 执行日志 | append |
| artifacts/*.md | Markdown | 用户 | 可分享学习产物 | atomic write |
| artifacts_index.jsonl | JSONL | 程序 | 产物索引 | append |

### 安全约束
- **path_safety**：所有文件写入前校验路径不离开项目根目录
- **secret redaction**：session_logger 自动脱敏 API Key、Token
- **atomic write**：index.json / profile.json / MEMORY.md 先写临时文件再 rename

---

## 目录结构

```
data/
├── memory/
│   ├── MEMORY.md              # 由 index.json 渲染（≤200行）
│   ├── index.json             # 唯一机器索引
│   └── learnings/             # 每次学习记录
│       └── 2026-05-10-rag.md
│
├── profile.json               # 用户画像 {version, updated_at, ...}
│
├── sessions/                  # 会话日志（含脱敏）
│   └── 2026-05-10-cli.jsonl
│
└── artifacts_index.jsonl      # 产物索引

artifacts/                     # 用户可读产物
├── summaries/
├── projects/
└── learning_paths/
```

---

## 关键数据格式

### index.json（source of truth）

```json
{
  "version": "1.1",
  "updated_at": "2026-05-10T15:30:00",
  "learnings": [
    {
      "id": "learning-20260510-rag",
      "topic": "RAG",
      "path": "data/memory/learnings/2026-05-10-rag.md",
      "type": "concept_summary",
      "source": "react_agent",
      "created_at": "2026-05-10T15:30:00",
      "tags": ["rag", "embedding", "retrieval"]
    }
  ],
  "recent_topics": ["RAG", "FastAPI", "LangGraph"]
}
```

### profile.json

```json
{
  "version": "1.1",
  "updated_at": "2026-05-10T15:30:00",
  "skills_known": ["Python"],
  "skills_learning": ["RAG", "LangGraph"],
  "preferred_difficulty": "beginner",
  "preferred_language": "python",
  "learning_goals": ["..."],
  "recent_topics": ["..."],
  "weak_points": ["..."],
  "completed_projects": [],
  "preferred_learning_style": "project_based"
}
```

### learnings/*.md

```markdown
---
id: learning-20260510-rag
topic: RAG
type: concept_summary
source: react_agent
created_at: 2026-05-10T15:30:00
difficulty: beginner
related_topics:
  - Embedding
  - Vector Search
artifact_path: artifacts/summaries/2026-05-10-rag-summary.md
---

# RAG 学习记录
## 用户问题
什么是 RAG？
## 核心概念
...
## 学习要点
1. ...
2. ...
## 后续建议
...
```

### sessions/*.jsonl（含脱敏）

```jsonl
{"time":"2026-05-10T15:00:00","type":"user_input","query":"我要学 FastAPI"}
{"time":"2026-05-10T15:00:01","type":"route","task_type":"complex","reason":"..."}
{"time":"2026-05-10T15:00:03","type":"plan_created","step_count":4}
{"time":"2026-05-10T15:00:05","type":"file_written","path":"projects/fastapi/main.py"}
{"time":"2026-05-10T15:00:06","type":"artifact_created","path":"artifacts/projects/fastapi-project.md"}
```

敏感字段（api_key、token 等）在写入前自动替换为 `[REDACTED]`。

### Plan-Execute 额外记录

```json
{"time":"...","type":"plan_execute_complete","project_dir":"projects/fastapi","generated_files":["main.py","requirements.txt"],"step_count":4}
```

路径用相对路径（避免暴露本机路径，便于跨机器迁移）。

---

## 搜索机制

`search_memory(query, limit=5) -> list[dict]`

1. 读 `index.json` 的 `learnings` 和 `recent_topics`
2. 对 `query` 做关键词匹配（分词后在 `topic`、`tags` 字段搜索）
3. 默认最多返回 3-5 条，只返回 metadata（topic / path / type / tags / created_at），**不读完整 .md 正文**
4. 真正需要详细内容时按 `path` 字段读取对应 .md
5. **不涉及向量搜索**（FAISS 延后到知识库）

---

## 工具层设计

### v1.1 工具范围

只保留 5 个核心工具：

| 工具 | 职责 | Provider | 风险 |
|------|------|----------|------|
| web_search | 搜索网页 title+url+snippet | TavilyProvider / MockProvider | low |
| content_fetch | 读取单个网页正文 | Jina Reader + httpx 降级 | low |
| github_disco | 搜索 GitHub 仓库 + README | GitHub API | low |
| filesystem | 写 projects/ 代码项目文件 | 本地文件系统 | medium |
| artifact_writer | 写 artifacts/ 学习产物 | 本地文件系统 | medium |

**v1.1 不做：** command_runner、test_runner、browser、slack/email 工具、LLM function calling 动态工具选择。

### 统一抽象

```
src/tools/
├── base.py            # ToolSpec, ToolResult, BaseTool
├── manager.py         # ToolManager (register/call/list)
├── errors.py          # ToolError, ConfigError, ProviderError
├── web_search.py      # 逻辑工具, TavilyProvider + MockProvider
├── content_fetch.py   # Jina Reader + httpx 降级
├── github_disco.py    # repo search + README
├── filesystem.py      # 写 projects/
└── artifact_writer.py # 写 artifacts/
```

### ToolResult（统一返回格式）

```python
class ToolResult(BaseModel):
    ok: bool
    tool_name: str
    data: dict | list | str | None = None
    error: str | None = None
    metadata: dict = {}
```

**所有工具必须返回 ToolResult，不直接抛异常。** 失败示例：

```json
{"ok": false, "tool_name": "web_search", "error": "missing TAVILY_API_KEY", "metadata": {"provider": "tavily"}}
```

### 调用链路

```
Agent
  → ToolManager.call("web_search", query=query)
    → Permission.is_allowed("web_search")
    → tool.run()
    → SessionLogger.log("tool_call", metadata_only=True)
  ← ToolResult
```

- Registry 只展示状态，**不执行工具**
- ToolManager 负责注册、权限检查、异常捕获、日志
- 工具调用日志只记录 metadata（url/provider/content_chars/truncated），**不记录完整网页正文和代码**

### web_search 作为逻辑工具

```
web_search ← 逻辑工具（Agent 调这个）
├── TavilyProvider   ← v1.1 默认
├── MockProvider     ← 测试用
└── 后续 BraveProvider / ExaProvider
```

配置：`WEB_SEARCH_PROVIDER=tavily`，切换 provider 不改 Agent 代码。

### content_fetch 安全约束

- 只允许 http/https
- **禁止** file://、localhost、127.0.0.1、内网 IP（防 SSRF）
- max_chars 默认 8000–12000
- 超时 10–20 秒
- 优先 Jina Reader，失败 → httpx + 正文抽取降级

### github_disco v1.1 范围

- `search_repos(query, limit)` — 搜索仓库
- `get_repo_readme(full_name)` — 获取 README
- **不做：** clone、源码分析、测试运行、PR、issue、commit history

### filesystem vs artifact_writer 边界

| | filesystem | artifact_writer |
|------|------|------|
| 写入目录 | projects/ | artifacts/ |
| 内容 | 代码项目文件 | 学习总结、项目说明 |
| 禁止写入 | artifacts/、.env、token 文件 | projects/、.env、token 文件 |
| 安全 | path_safety | path_safety |

### 工具失败降级策略

| 工具失败 | 降级行为 |
|------|------|
| web_search | 提示未联网，基于已有知识回答 |
| content_fetch | 用 web_search 的 snippet 继续 |
| github_disco (缺 token) | disabled，不影响普通学习 |
| filesystem | 返回错误，输出内容但提示未保存 |
| artifact_writer | 不影响回答，只提示保存失败 |
| session_logger | 不影响主流程 |

**核心原则：学习 > 工具副作用。** 工具失败不能中断核心学习流程。

### /status 工具层展示

```
🔧 工具层 Tools
  web_search       ✓ | provider=tavily | key=configured | risk=low
  content_fetch    ✓ | provider=jina+httpx | risk=low
  github_disco     ✗ | missing GITHUB_TOKEN | risk=low
  filesystem       ✓ | root=projects/ | overwrite=false | risk=medium
  artifact_writer  ✓ | root=artifacts/ | risk=medium
```

---

## 任务清单

### Phase 1：基础设施

**任务 1：依赖更新**
- `pyproject.toml`：删除 `chromadb`、`aiosqlite`，添加 `pyyaml`
- 注意：不删除 `short_term.py` 源码，迁移其测试后再处理

**任务 2：数据结构 `src/memory/schemas.py`**
- MemoryType 枚举、Frontmatter、MemoryIndex、UserProfileData、SessionEvent、ArtifactRecord Pydantic 模型
- 模型自带合法性校验（必填字段、类型约束）

**任务 3：Registry `src/registry/`**
- `registry.py`：模块注册、`status()`（只读面板）
- `validator.py`：启动时校验必填 Key（LLM_PROVIDER、对应 API Key 等），友好提示
- `permission.py`：读 `.env` 中 TOOL_* / EXT_* 开关，`is_allowed(module)` 接口

**任务 4：工具层基础设施 `src/tools/base.py` + `manager.py`**
- `ToolSpec`：name / description / provider / enabled / required_config / risk_level
- `ToolResult(ok, tool_name, data, error, metadata)`：统一返回格式，不抛异常
- `BaseTool`：统一 `async run(**kwargs) -> ToolResult` 接口
- `ToolManager`：`register()` / `list_tools()` / `call(name, **kwargs)`
- `call()` 内部完成：注册检查 → 启用检查 → permission → try/except → session log
- `errors.py`：ToolError / ConfigError / ProviderError
- web_search 重构为 TavilyProvider + MockProvider 结构
- 所有工具迁移到统一 ToolResult 返回
- 测试：ToolResult 序列化、ToolManager 注册/禁用/未注册、MockProvider

**任务 5：Prompt Registry `src/core/prompts/`**
- 只做 `load_prompt(name: str) -> str`
- 目录：`src/core/prompts/{router,summarize,plan_execute}.md`
- **不做**：版本号、热更新、多语言、模板继承

### Phase 2：记忆层

**任务 6：索引管理 `src/memory/index_manager.py`**
- `index.json` 是唯一 source of truth
- 读写接口：`add_learning(entry)`、`list_all()`、`get_recent(limit)`
- `render_memory_md(index)`：每次全量重新生成 MEMORY.md（单向渲染）
  - 固定 header
  - profile 位置说明
  - recent_topics（最近 10 条）
  - 最近 20 条 learnings 摘要
  - artifacts 位置说明
  - ≤200 行（自然约束，不做截断）
- **atomic write**：先写 `.tmp` → `os.replace` → 目标文件

**任务 7：学习记录 `src/memory/learning_recorder.py`**
- `save_learning(topic, summary: KnowledgeSummary)`：
  - 生成 `learnings/<date>-<slug>.md`（YAML frontmatter + markdown 正文）
  - 更新 `index.json`
  - 调用 index_manager 重新渲染 MEMORY.md
- `search_memory(query)`：基于 index.json 的关键词匹配
- `get_recent_learnings(limit)`

**任务 8：用户画像 `src/memory/user_profile.py`**
- 保持 `profile.json` 格式，扩展 `version`、`updated_at` 字段
- `update_profile(topic)`：
  - 追加 `skills_learning` + `recent_topics`（去重）
  - **不自动加入 `skills_known`**（需完成项目或多次学习后手动/规则升级）
- `mark_skill_known(topic)`：从 skills_learning 移到 skills_known
- 兼容旧 `data/profile.json` 自动迁移
- **atomic write**

**任务 9：会话日志 `src/memory/session_logger.py`**
- `SessionLogger` 类：追加 `sessions/<date>-<mode>.jsonl`
- `log(event_type, data)`：自动注入 timestamp
- **secret redaction** 两层规则：
  - 字段名命中 → 直接替换值（api_key, apikey, token, secret, authorization, password 及其变体）
  - 值命中密钥模式 → 替换（`sk-...`, `Bearer ...`, `ghp_...`, `tvly-...`, `jina_...`）
  - 不误删普通文本（如 "keyboard"）
- **日志用相对路径**：sessions 和 plan_execute_complete 中的路径尽量用相对路径
- 特殊事件：`plan_execute_complete` 记录 `project_dir` + `generated_files`

**任务 10：路径安全 `src/utils/path_safety.py`**
- `safe_path(base_dir, relative_path) -> Path`：
  - `base = Path(base_dir).resolve()`
  - `target = (base / relative_path).resolve()`
  - `target.relative_to(base)` → 验证不穿越
  - 可防御 `../`、绝对路径、软链接跳出
- `safe_write(path, content)`：atomic write 封装（先写 `.tmp` → `os.replace`）
- artifact_writer 和 filesystem 统一使用

**任务 11：Artifact `src/tools/artifact_writer.py`**
- 输出文件名带日期/时间，避免覆盖：
  - `artifacts/summaries/2026-05-10-rag-summary.md`
  - `artifacts/projects/2026-05-10-fastapi-project.md`
  - 或 `artifacts/summaries/rag-20260510-1530.md`
- 追加 `data/artifacts_index.jsonl`（含唯一 artifact_id）
- Plan-Execute 产物记录 generated_files 列表
- 所有写入通过 `path_safety` 校验

### Phase 3：接入

**任务 12：Agent 接入记忆**
- `react_agent.py`：添加 `memory_manager` 参数，成功后自动 save_learning + update_profile + write_artifact
- `plan_execute_agent.py`：summarize_node 保存 learning + generated_files 信息
- `main.py`：启动初始化管理器、CLI 显示最近学习、查询前 search_memory
- **核心约束：记忆失败不能阻塞主流程**
  - profile.json 解析失败 → warning → 创建默认 profile
  - memory index 不存在 → 自动初始化
  - artifact 写入失败 → 不影响最终回答，提示"保存失败"
  - memory_manager 为 None → 不尝试写入，不做任何记忆操作
- 现有 33 个测试必须保持通过

**任务 13：CLI 命令面板**
- `/status` — 模块状态（Registry 驱动，只读）
- `/history` — 最近学习记录
- `/profile` — 当前用户画像
- `/memory` — 搜索记忆关键词

### Phase 4：评估 & 收尾

**任务 14：评估框架 `src/eval/`**
- 10+ 测试 query 数据集
- 路由正确性评分
- 输出完整性检查
- 文件格式合法性测试（JSON / JSONL / YAML frontmatter）
- 路径安全测试
- frontmatter 解析测试
- **所有测试使用 tmp_path，不依赖真实 API Key**
- 原有 33 个测试必须继续通过

**任务 15：迁移和清理**
- 检查 `short_term.py` 的引用
- 迁移 `test_short_term.py` 中有价值的测试到新模块
- `short_term.py` + `test_short_term.py` 标注 deprecated：
  - 仅在类初始化时 `warnings.warn(..., DeprecationWarning, stacklevel=2)`
  - 不在普通运行时反复刷警告
- 暂不删除这两个文件
- 验证 `.gitignore` 中 `data/` 已生效

**任务 16：全量验证**
- `make lint` 零错误
- `make test` 全部通过
- CLI 手动验证：
  1. 首次启动：显示"新用户"
  2. `什么是RAG`：学习后 data/memory/learnings/ 有新文件
  3. data/profile.json 已更新 RAG 到 skills_learning（simple 学习不升级 skills_known）
  4. data/sessions/ 有当次会话日志
  5. artifacts/summaries/ 有产物
  6. 退出重开 → `/history` 显示 RAG
  7. `/status` 显示所有模块状态
  8. 删除 API Key → 启动有友好提示
