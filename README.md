# LearnAgent

面向自学者的 AI 学习助手。帮助用户完成「发现新技术 → 理解核心概念 → 阅读资料/仓库 → 动手实践 → 复盘总结」的完整学习闭环。

---

## 架构

```
用户输入
  → LLM Router（意图分类）
  → LearnQueryEngine（会话编排 + Skill 注入 + Topic 管理）
  → ContextBuilder（Static + Dynamic + Skill 三段 prompt）
  → Agent Loop（LLM ↔ Tool 多轮循环）
    → Permission（只读自动/写入确认/Plan Mode 写入禁止）
    → Tool 执行（内置 8 个工具 + MCP 外部工具）
    → tool_result 回填
  → LLM 最终回复
  → Session 持久化（JSONL）+ Memory 持久化（Markdown + Frontmatter）
```

---

## 功能概览

### LLM 层

| 组件 | 说明 |
|---|---|
| `LLMClient` | 抽象基类，统一 `chat` / `stream_chat` 接口 |
| `MockLLMClient` | 确定性 mock，支持 tool_use/tool_turns 多轮模拟 |
| `DeepSeekLLMClient` | OpenAI-compatible API，httpx 异步，payload 清洗 |
| `ModelSelector` | 规则路由：normal → V4 Flash，deep/planning → V4 Pro |
| `LLMRouter` | LLM 驱动的意图分类，5 类识别 |

### 工具层

| 工具 | 类型 | 实现 |
|---|---|---|
| `search_web` | 只读 | DuckDuckGo（ddgs），返回 title/url/snippet |
| `read_url` | 只读 | httpx + BeautifulSoup4 正文提取，regex 降级 |
| `analyze_github_repo` | 只读 | raw.githubusercontent.com + GitHub API（免 token） |
| `file_write` | 写入 | workspace 内创建文件，路径安全校验，拒绝保留名 |
| `file_read` | 只读 | workspace 内读取文件，长内容截断 |
| `run_code` | 执行 | subprocess + Docker Sandbox 可选，超时/输出截断，15 项危险命令过滤 |
| `list_files` | 只读 | workspace 文件树，限制深度和条目数 |
| `learning_todo_write` | 写入 | 学习任务进度跟踪 |

所有工具通过 ToolRegistry 统一注册，支持 Mock/Real 双模式，CLI 通过 `--real` 切换。

### Skill 系统

| Skill | 触发意图 | 工作流 |
|---|---|---|
| `learn-concept` | learn_concept | 搜索 → 解释 → 拆解 → 示例 → 路线 → 练习 → Todo |
| `read-repo` | analyze_repo | 分析 → 搜索 → 总结 → 技术栈 → 模块 → 设计点 → 阅读顺序 |
| `review-progress` | review | 回顾 → 自评 → 费曼技巧 → 加强点 → 建议 → 更新计划 |

Skills 通过 SKILL.md 定义，QueryEngine 根据 Router 识别的意图自动注入对应 Skill 指令。

### 编排与安全

| 功能 | 说明 |
|---|---|
| Agent Loop | LLM ↔ Tool 多轮循环，max_turns 保护，tool_use/tool_result 对齐 |
| Plan Mode | `/plan` 进入只读模式，LLM 探索资料后输出计划，确认后执行 |
| Permission | 只读自动通过，写入/执行确认（60s Trust Window 免重复） |
| Docker Sandbox | RunCode 可选容器隔离（256MB/1CPU/无网络） |
| Token Budget | 消息超 ~8000 tokens 自动压缩旧消息为摘要 |
| Topic 管理 | 自动规范化和漂移检测，workspace 按 topic 隔离 |

### MCP（Model Context Protocol）

- JSON-RPC 2.0 over stdio 客户端
- 通过 `.mcp.json` 配置外部工具服务器
- MCPToolAdapter 将外部工具包装为 Tool 接口
- 命名空间隔离：`mcp__{server}__{tool}`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-filesystem", "."]
    }
  }
}
```

### 持久化

| 存储 | 格式 | 说明 |
|---|---|---|
| Session | JSONL | `storage/sessions/<id>.jsonl`，支持 `--resume` 恢复 |
| Memory | Markdown + YAML | `storage/memory/*.md`，跨会话共享 |

### CLI 命令

```
/help        查看可用命令
/plan        进入/退出计划模式（只读探索 → 确认 → 执行）
/topic       查看或切换学习主题
/progress    查看学习进度
/sessions    列出历史会话
/model       显示当前模型
/tools       列出已注册工具（含 MCP 工具）
/memory      查看长期记忆
/status      查看系统状态
/clear       清空当前会话
/exit        退出
```

---

## 快速开始

### 安装

```bash
git clone git@github.com:DengYijunX/LearnAgent.git
cd LearnAgent
pip install -e .
```

### 配置

```bash
cp .env.example .env
# 编辑 .env，填写 DEEPSEEK_API_KEY
```

### 运行

```bash
# Mock 模式（无需 API key，验证架构）
python -m app.main

# 真实模式（需要 .env 配置）
python -m app.main --real

# 恢复最近会话
python -m app.main --real --resume latest
```

### MCP 配置（可选）

```bash
cp .mcp.example.json .mcp.json
# 编辑 .mcp.json，配置外部工具服务器
```

### 测试

```bash
# 单元测试（mock，无需网络，135 个用例）
pytest tests/ -v

# 真实集成测试（需要 API key + 网络）
RUN_REAL_TESTS=1 pytest tests/ -v

# LLM 冒烟测试
python scripts/smoke_llm_real.py

# 沙箱自动化测试
python scripts/sandbox_test.py --real
```

---

## 目录结构

```
LearnAgent/
├── app/
│   ├── main.py                    # CLI 入口
│   ├── config/settings.py         # 配置（.env → Config）
│   ├── llm/                       # LLM 通信层
│   │   ├── base.py                # LLMClient 抽象
│   │   ├── mock_client.py         # Mock 实现
│   │   ├── deepseek_client.py     # DeepSeek 适配器
│   │   └── model_selector.py      # 模型选择器
│   ├── tools/                     # 工具层
│   │   ├── base.py                # Tool 基类
│   │   ├── registry.py            # ToolRegistry
│   │   ├── search_web.py          # 搜索（Mock + Real）
│   │   ├── read_url.py            # 网页读取（Mock + Real）
│   │   ├── github_analyzer.py     # 仓库分析（Mock + Real）
│   │   ├── workspace_tools.py     # 文件读写 + 代码执行
│   │   └── todo_tools.py          # 学习任务管理
│   ├── core/                      # 编排层
│   │   ├── agent_loop.py          # Agent 循环 + 事件回调
│   │   ├── query_engine.py        # 会话编排 + Skill/Topic 管理
│   │   ├── llm_router.py          # LLM 意图分类器
│   │   └── router.py              # 正则路由器（降级）
│   ├── context/                   # 上下文层
│   │   ├── context_builder.py     # Static + Dynamic + Skill + Plan
│   │   └── compaction.py          # Token Budget + 上下文压缩
│   ├── memory/                    # 记忆层
│   │   ├── session_store.py       # JSONL 会话存储
│   │   └── memory_store.py        # Markdown 长期记忆
│   ├── safety/                    # 安全层
│   │   └── permission.py          # allow/ask/deny 权限
│   ├── skills/                    # Skill 加载器
│   │   └── loader.py              # SKILL.md 解析
│   └── mcp/                       # MCP 集成
│       ├── client.py              # JSON-RPC 2.0 客户端
│       ├── adapter.py             # MCP → Tool 适配器
│       └── loader.py              # .mcp.json 配置加载
├── skills/                        # Skill 定义
│   ├── learn-concept/SKILL.md
│   ├── read-repo/SKILL.md
│   └── review-progress/SKILL.md
├── tests/                         # 135 个测试用例
├── docs/                          # 设计文档 + 决策记录
│   ├── agent_design_reference_full.md
│   ├── learnagent_architecture_design_v1.md
│   ├── decisions.md               # 12 条架构决策
│   └── resume-project-analysis.md
├── scripts/
│   ├── smoke_llm_real.py          # LLM 连通性测试
│   └── sandbox_test.py            # 自动化端到端测试
├── storage/                       # 运行时数据（.gitignore）
│   ├── sessions/
│   ├── memory/
│   └── workspace/
├── pyproject.toml
├── .env.example
├── .mcp.example.json
└── README.md
```

---

## 技术栈

- Python >= 3.10
- LLM：DeepSeek V4 Flash / V4 Pro（OpenAI-compatible API）
- 搜索：ddgs（DuckDuckGo）
- 网页解析：BeautifulSoup4 + httpx
- 依赖：python-dotenv / pyyaml / click
- 测试：pytest + pytest-asyncio（135 用例）

## 分支

- `main` — 稳定分支
- `agent/claude-rebuild` — Claude Code 从零构建路线
- `agent/codex-rebuild` — Codex 从零构建路线
