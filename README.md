# LearnAgent

面向自学者的 AI 学习助手。帮助用户完成「发现新技术 → 理解核心概念 → 阅读资料/仓库 → 动手实践 → 复盘总结」的完整学习闭环。

## 第一阶段成果

14 个提交，106 个测试，8 个工具，3 个学习 Skill。

### 架构

```
用户输入
  → InputRouter（规则匹配 5 种意图）
  → LearnQueryEngine（会话编排 + Skill 注入）
  → ContextBuilder（Static + Dynamic + Skill 三段 prompt）
  → Agent Loop（LLM ↔ Tool 循环）
    → Permission（allow / ask / deny）
    → Tool 执行（8 个工具）
    → tool_result 回填
  → LLM 最终回复
  → Session 持久化（JSONL）+ Memory 持久化（Markdown）
```

### LLM 层

| 组件 | 说明 |
|---|---|
| `LLMClient` | 抽象基类，统一 `chat` / `stream_chat` 接口 |
| `MockLLMClient` | 确定性 mock，支持 tool_use/tool_turns 参数控制 |
| `DeepSeekLLMClient` | OpenAI-compatible API，httpx 异步调用，payload 清洗 |
| `ModelSelector` | 规则映射：normal → V4 Flash，deep/planning/repo_analysis → V4 Pro |

### 工具层（8 个工具）

| 工具 | 类型 | 说明 |
|---|---|---|
| `search_web` | 只读 | Mock + Real（DuckDuckGo），搜索技术资料 |
| `read_url` | 只读 | Mock + Real（httpx + HTML 提取），读取网页正文 |
| `analyze_github_repo` | 只读 | Mock + Real（免 token），读取 README + 仓库元信息 |
| `file_write` | 写入 | 在 workspace 内创建文件，自动建目录，拒绝路径逃逸 |
| `file_read` | 只读 | 读取 workspace 内文件，支持截断 |
| `run_code` | 执行 | asyncio subprocess，超时 + 输出截断保护 |
| `list_files` | 只读 | 列出 workspace 文件树 |
| `learning_todo_write` | 写入 | 学习任务进度管理 |

### Skill 系统

| Skill | 触发意图 | 工作流步骤 |
|---|---|---|
| `learn-concept` | `learn_concept` | 搜索资料 → 解释概念 → 拆解 → 示例 → 学习路线 → 练习 → Todo |
| `read-repo` | `analyze_repo` | 分析仓库 → 搜索补充 → 总结 → 技术栈 → 模块 → 设计点 → 阅读顺序 → 模仿项目 |
| `review-progress` | `review` | 回顾记忆 → 自评 → 费曼技巧 → 加强点 → 下阶段建议 → 更新计划 |

### 持久化

| 存储 | 格式 | 目录 |
|---|---|---|
| Session | JSONL 逐行追加 | `storage/sessions/<session_id>.jsonl` |
| Memory | Markdown + YAML frontmatter | `storage/memory/*.md` |

### CLI 命令

```
/help      查看可用命令
/topic     查看或切换学习主题
/progress  查看学习进度
/model     显示当前模型
/tools     列出已注册工具
/memory    查看长期记忆
/clear     清空当前会话
/exit      退出
```

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
# Mock 模式（无需 API key，用于验证架构）
python -m app.main

# 真实模式（需要配置 .env）
python -m app.main --real
```

### 冒烟测试

```bash
# 验证 DeepSeek API 连通性
python scripts/smoke_llm_real.py
```

### 测试

```bash
# 全部单元测试（mock，无需网络）
pytest tests/ -v

# 真实集成测试（需要 API key + 网络）
RUN_REAL_TESTS=1 pytest tests/ -v
```

## 目录结构

```
LearnAgent/
├── app/
│   ├── main.py                  # CLI 入口
│   ├── config/settings.py       # 配置模块（.env → Config）
│   ├── llm/                     # LLM 通信层
│   │   ├── base.py              # LLMClient 抽象
│   │   ├── mock_client.py       # Mock 实现
│   │   ├── deepseek_client.py   # DeepSeek 适配器
│   │   └── model_selector.py    # 模型选择器
│   ├── tools/                   # 工具层
│   │   ├── base.py              # Tool 基类
│   │   ├── registry.py          # ToolRegistry
│   │   ├── search_web.py        # Mock + Real 搜索
│   │   ├── read_url.py          # Mock + Real 网页读取
│   │   ├── github_analyzer.py   # Mock + Real 仓库分析
│   │   ├── workspace_tools.py   # FileWrite/Read/RunCode/ListFiles
│   │   └── todo_tools.py        # LearningTodoWrite
│   ├── core/                    # 编排层
│   │   ├── agent_loop.py        # Agent 循环
│   │   ├── query_engine.py      # 会话编排 + Skill 注入
│   │   └── router.py            # 输入路由器
│   ├── context/                 # 上下文层
│   │   └── context_builder.py   # Static + Dynamic + Skill
│   ├── memory/                  # 记忆层
│   │   ├── session_store.py     # JSONL 会话存储
│   │   └── memory_store.py      # Markdown 长期记忆
│   ├── safety/                  # 安全层
│   │   └── permission.py        # 权限系统
│   └── skills/                  # Skill 加载器
│       └── loader.py            # SKILL.md 解析器
├── skills/                      # Skill 定义
│   ├── learn-concept/SKILL.md
│   ├── read-repo/SKILL.md
│   └── review-progress/SKILL.md
├── scripts/
│   └── smoke_llm_real.py        # LLM 冒烟测试
├── tests/                       # 106 个测试
├── docs/
│   ├── agent_design_reference_full.md
│   ├── learnagent_architecture_design_v1.md
│   ├── decision-confirmation-rules.md
│   └── decisions.md             # 架构决策记录
├── pyproject.toml
├── .env.example
└── README.md
```

## 分支策略

- `main`：稳定分支
- `agent/claude-rebuild`：Claude Code 从零构建路线
- `agent/claude-continue`：基于已有实现继续演进
- `agent/codex-rebuild`：Codex 从零构建路线

## 技术栈

- Python >= 3.10
- LLM：DeepSeek V4 Flash / V4 Pro（OpenAI-compatible API）
- 搜索：ddgs（DuckDuckGo）
- HTTP：httpx（异步）
- CLI：标准 input/print
- 测试：pytest + pytest-asyncio
- 配置：python-dotenv
