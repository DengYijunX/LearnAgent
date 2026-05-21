# Architecture Decision Records

## Decision 001：LLM 服务商选择 DeepSeek

**日期：** 2026-05-20

**状态：** Accepted

**背景：**

项目第一阶段需要接入真实 LLM 作为 Agent 基座。原设计文档推荐 SiliconFlow + Qwen/Qwen2.5-7B-Instruct，但考虑到 tool calling 稳定性、模型能力和已有使用经验，调整为 DeepSeek。

**决策：**

使用 DeepSeek 作为第一阶段主要 LLM 服务商，接口采用 OpenAI-compatible API。

**理由：**

1. DeepSeek tool calling 在同类模型中稳定性更好。
2. 项目已有 DeepSeek 使用经验。
3. OpenAI-compatible API 切换成本低，后续可扩展多 provider。
4. V4 Flash 作为日常默认模型兼顾成本和速度，V4 Pro 用于复杂任务。

**影响：**

1. 需要 DEEPSEEK_API_KEY 和 DEEPSEEK_BASE_URL 配置项。
2. LLMClient 需要支持 DeepSeek 和 mock 两种实现。
3. 需要 ModelSelector 根据模式选择小/大模型。

---

## Decision 002：双模型策略

**日期：** 2026-05-20

**状态：** Accepted

**背景：**

不同学习任务对模型能力要求不同：简单概念解释可用轻量模型，复杂仓库分析和架构设计需要强推理模型。

**决策：**

- **小模型（DeepSeek V4 Flash）**：用于 normal / summary / lightweight / learn_concept 等日常任务。
- **大模型（DeepSeek V4 Pro）**：用于 deep / planning / repo_analysis / architecture_design 等复杂任务。
- 第一阶段 ModelSelector 使用简单规则映射，不做复杂智能调度。

**理由：**

1. 日常任务用大模型浪费成本和延迟。
2. 复杂任务用小模型可能推理不充分。
3. 简单规则映射可测试、可理解、可后续扩展。

**影响：**

1. Config 需要 small_model 和 large_model 两个字段。
2. ModelSelector 需要实现 mode → model 映射。
3. Workflow 不直接决定模型名，通过 ModelSelector 获取。

---

## Decision 003：项目形态 - CLI First

**日期：** 2026-05-20

**状态：** Accepted

**背景：**

项目需要快速验证 Agent Loop 和 Tool 系统，Web UI 会引入额外复杂性。

**决策：**

第一阶段实现 Python CLI 原型（使用 click），暂不引入 FastAPI、Flask 或前端。

**理由：**

1. CLI 开发最快、调试最方便。
2. 当前重点是核心 Agent 流程，不是 UI。
3. CLI 和后续 API 可复用同一套核心 workflow。

**影响：**

1. 入口点在 app/main.py 或 app/entrypoint/cli.py。
2. 核心逻辑与 CLI 层解耦。
3. 后续扩展 FastAPI 时无需改 workflow。

---

## Decision 004：Memory 存储方式

**日期：** 2026-05-20

**状态：** Accepted

**背景：**

Agent 需要区分短期会话流水和长期学习记忆。

**决策：**

- **Session / workflow trace：JSONL**（追加写入、便于解析和恢复）
- **长期学习记忆：Markdown + frontmatter**（人类可读、git diff 友好、可手动编辑）
- 存储目录：`storage/sessions/`、`storage/memory/`、`storage/runs/`

**理由：**

1. JSONL 适合流式追加和逐行解析，适合会话记录。
2. Markdown + frontmatter 适合长期记忆，与 Claude Code Memory 设计一致。
3. 预留抽象接口，后续可替换为 SQLite / 向量数据库。

**影响：**

1. `storage/` 必须加入 `.gitignore`。
2. MemoryStore 和 SessionStore 需要抽象接口。
3. 不上传用户数据到第三方。

---

## Decision 005：外部服务接入策略

**日期：** 2026-05-20

**状态：** Accepted

**背景：**

Web Search 和 GitHub API 对学习场景有价值，但第一阶段需要控制复杂度和外部依赖。

**决策：**

- **Web Search**：第一阶段做抽象接口 + mock，预留 RealSearchTool 位置。
- **GitHub API**：第一阶段不接入，仅支持公开 README/URL 读取，通过 GitHubAnalyzer 抽象接口预留。
- **真实 LLM**：第一阶段接入，通过 smoke test 验证。

**理由：**

1. 搜索 API 涉及付费、配额、反爬等复杂问题。
2. GitHub API 需要 token 和 rate limit 管理。
3. 先用 mock 验证架构，后续按需接入。

**影响：**

1. SearchWeb 工具需要抽象接口。
2. GitHubAnalyzer 需要抽象接口。
3. `scripts/smoke_llm_real.py` 用于验证真实 LLM 可用。
4. `RUN_REAL_TESTS=1` 控制集成测试开关。

---

## Decision 006：Tool Calling Fallback 策略

**日期：** 2026-05-20

**状态：** Accepted

**背景：**

部分模型的标准 tool calling 可能不稳定，需要 fallback 机制。

**决策：**

- 优先使用标准 OpenAI tool calling 格式。
- 如果模型 tool calling 不稳定，允许使用 JSON action 格式作为 fallback：
  `{"action": "search_web", "arguments": {"query": "..."}}`
- LLMClient / AgentLoop 应隔离不同模型的工具调用格式差异。

**理由：**

1. 标准 tool calling 是首选，兼容性最好。
2. JSON action fallback 作为保险，不阻塞开发。
3. 格式差异应封装在 LLMClient 层，不污染 AgentLoop。

**影响：**

1. AgentLoop 需要支持两种 tool call 解析方式。
2. LLMClient 应尽量屏蔽格式差异。
3. JSON action 和业务逻辑不应强耦合。

---

## Decision 007：测试策略

**日期：** 2026-05-20

**状态：** Accepted

**背景：**

项目需要测试，但不能让测试依赖外部网络和付费 API。

**决策：**

- **单元测试**：默认使用 mock（MockLLMClient、MockSearchTool 等），不依赖网络。
- **真实集成测试**：默认跳过，仅当 `RUN_REAL_TESTS=1` 且 API key 存在时运行。
- **Smoke test**：LLMClient 完成后提供 `scripts/smoke_llm_real.py` 手动验证。
- **测试框架**：pytest + pytest-asyncio。

**理由：**

1. Mock 测试快速、稳定、零成本。
2. 真实测试按需运行，不阻塞 CI。
3. Smoke test 提供快速手动验证真实 API 的能力。

**影响：**

1. 所有外部能力先定义抽象接口，再提供 mock 和真实实现。
2. 真实集成测试使用 `@pytest.mark.skipif` 条件跳过。
3. `RUN_REAL_TESTS` 作为 feature flag 控制。

---

## Decision 008：真实搜索使用 DuckDuckGo（ddgs）

**日期：** 2026-05-21

**状态：** Accepted

**背景：**

第一阶段需要接入真实 Web Search，但付费搜索 API 涉及成本、配额和注册流程。

**决策：**

使用 `ddgs`（DuckDuckGo Search）作为真实搜索后端，免费、无需 API key。

**理由：**

1. 零成本、零注册，适合开发阶段。
2. 返回 title / url / snippet 三元组，满足学习资料检索需求。
3. `ddgs` 是 `duckduckgo_search` 的新版替代，API 更稳定。

**影响：**

1. 新增依赖 `ddgs`。
2. `RealSearchWeb` 和 `MockSearchWeb` 共享 `name: search_web`，CLI 根据 `--real` 选择。
3. 搜索结果噪声可能较高，LLM 需要自行筛选。

---

## Decision 009：GitHub 仓库分析免 token 实现

**日期：** 2026-05-21

**状态：** Accepted

**背景：**

GitHub 仓库分析是学习场景的重要需求，但 GitHub API token 涉及权限管理。

**决策：**

第一阶段使用免 token 方式：
- README：`raw.githubusercontent.com` 直接获取（尝试 main/master 分支）
- 仓库信息：`api.github.com/repos/{owner}/{repo}`（公开仓库免认证）
- 两者都失败则返回错误

**理由：**

1. 避免 token 管理的复杂度。
2. 公开仓库的 README 和元信息已足够学习分析。
3. 后续如需深度分析（文件树、commit 历史），再引入 GitHub API token。

**影响：**

1. `RealGitHubAnalyzer` 无需任何认证配置。
2. 私有仓库无法分析（预期行为）。
3. GitHub API 有未认证 rate limit（60 次/小时），足够学习场景使用。

---

## Decision 010：Session/Memory 双轨持久化

**日期：** 2026-05-21

**状态：** Accepted

**背景：**

Agent 需要区分短期会话流水和长期学习记忆。

**决策：**

- **Session**：JSONL 格式，逐行追加，保存于 `storage/sessions/<session_id>.jsonl`。
- **Memory**：Markdown + YAML frontmatter，保存于 `storage/memory/*.md`。
- 学习意图（learn_concept / analyze_repo / review）自动触发 Memory 写入。
- `storage/` 目录加入 `.gitignore`，不上传到 Git。

**理由：**

1. JSONL 适合逐行追加和恢复，适合会话记录。
2. Markdown + frontmatter 人类可读、可手动编辑、git diff 友好。
3. 自动写入降低用户操作负担，同时避免垃圾记忆（仅学习意图触发）。

**影响：**

1. `storage/` 必须在 `.gitignore` 中。
2. `QueryEngine` 接受 `session_store` 和 `memory_store` 注入。
3. 后续可替换为 SQLite / 向量数据库，只需实现相同接口。

---

## Decision 011：Skill 系统根据意图自动注入

**日期：** 2026-05-21

**状态：** Accepted

**背景：**

设计文档定义了 learn-concept / read-repo / review-progress 等 Skill，但需要在 Agent Loop 中生效。

**决策：**

- QueryEngine 根据 Router 识别的 intent 自动匹配 Skill。
- 映射：`learn_concept` → `learn-concept`，`analyze_repo` → `read-repo`，`review` → `review-progress`。
- Skill body 注入 system prompt 的 `<SKILL>` 标签段。
- Skill 定义和业务代码解耦，通过 SKILL.md 文件管理。

**理由：**

1. 自动注入减少用户操作，学习流程更顺畅。
2. SKILL.md 独立文件便于人工编辑和版本控制。
3. 映射关系集中在 `INTENT_TO_SKILL` 字典，后续可扩展。

**影响：**

1. `ContextBuilder.build_system_prompt()` 新增 `skill_body` 参数。
2. Skill 文件放在 `skills/` 目录，CLI 启动时自动加载。
3. Skills 变更不需要改代码。

---

## Decision 012：Workspace 工具参考 Claude Code 设计

**日期：** 2026-05-21

**状态：** Accepted

**背景：**

学习闭环缺少实践环节，用户需要创建项目文件、阅读和运行代码。

**决策：**

参考 Claude Code 的 Read/Write/Bash 工具设计，实现 workspace 工具：
- `file_write` / `file_read`：文件读写，所有路径解析后必须在 `workspace_root` 内。
- `run_code`：asyncio subprocess 执行，超时 30s + 输出截断 5000 字符。
- `list_files`：列出 workspace 文件树。
- 路径安全：拒绝绝对路径和 `../` 逃逸。
- 权限：file_write 和 run_code 为 `is_read_only=False`，触发 ask 权限。
- RunCode 暂不做 Docker 沙箱（Phase 2）。

**理由：**

1. Claude Code 这套工具设计经过大量实战验证，路径限制 + 权限 + 截断三层保护成熟可靠。
2. 学习场景只需基础文件操作和代码执行，不需要完整的 Shell 能力。
3. 路径逃逸拒绝是安全底线。
4. Docker 沙箱可在 Phase 2 按需引入。

**影响：**

1. 新增 `app/tools/workspace_tools.py`（4 个工具类）。
2. workspace 目录位于 `storage/workspace/`。
3. RunCode 在 Windows 上 timeout 行为与 Unix 不同，相关测试标记 skip。
