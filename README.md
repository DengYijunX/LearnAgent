# LearnAgent

面向自学者的 AI 学习助手 —— 帮助用户完成「发现新技术 → 理解核心概念 → 阅读资料/仓库 → 动手实践 → 复盘总结」的学习闭环。

## 项目状态

**当前分支：** `agent/claude-rebuild`（Claude Code 从零构建路线）

**第一阶段（MVP）已完成：**

- [x] 配置模块（`.env` + `app/config/settings.py`）
- [x] LLMClient 抽象 + Mock 实现 + DeepSeek 适配器
- [x] ModelSelector（基于模式的规则模型选择）
- [x] Tool 基类 + ToolRegistry
- [x] Agent Loop（LLM ↔ Tool 最小闭环）
- [x] InputRouter（规则匹配识别输入类型）
- [x] LearnQueryEngine（会话编排器）
- [x] ContextBuilder（Static + Dynamic 上下文）
- [x] SessionStore（JSONL 会话流水）
- [x] MemoryStore（Markdown + frontmatter 长期记忆）
- [x] Permission（allow / ask / deny 权限）
- [x] learn-concept Skill 定义
- [x] CLI 入口（Mock 模式 + 真实 API 模式）
- [x] LLM 冒烟测试脚本

## 快速开始

### 安装

```bash
# 克隆仓库
git clone git@github.com:DengYijunX/LearnAgent.git
cd LearnAgent

# 安装依赖
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

# 真实 API 模式（需要配置 .env）
python -m app.main --real
```

### 冒烟测试

```bash
# 验证 DeepSeek API 连通性
python scripts/smoke_llm_real.py
```

### 运行测试

```bash
# 全部单元测试（mock 模式，无需网络）
pytest tests/ -v

# 真实集成测试（需要 DEEPSEEK_API_KEY）
RUN_REAL_TESTS=1 pytest tests/ -v
```

## 架构

```
用户输入 → Router → LearnQueryEngine → ContextBuilder → Agent Loop
  → LLM Client → Tool Registry → Permission → Tool 执行
  → tool_result → LLM → 最终输出 → Memory 保存
```

```
app/
├── main.py              # CLI 入口
├── config/settings.py   # 配置模块
├── llm/                 # LLM 通信层
│   ├── base.py          # LLMClient 抽象
│   ├── mock_client.py   # Mock 实现
│   ├── deepseek_client.py # DeepSeek 适配器
│   └── model_selector.py  # 模型选择器
├── tools/               # 工具层
│   ├── base.py          # Tool 基类
│   └── registry.py      # ToolRegistry
├── core/                # 编排层
│   ├── agent_loop.py    # Agent 循环
│   ├── query_engine.py  # 会话编排器
│   └── router.py        # 输入路由器
├── context/             # 上下文层
│   └── context_builder.py
├── memory/              # 记忆层
│   ├── session_store.py # JSONL 会话存储
│   └── memory_store.py  # Markdown 长期记忆
├── safety/              # 安全层
│   └── permission.py    # 权限系统
└── skills/              # 技能加载器
    └── loader.py
```

## 分支策略

- `main`：稳定分支
- `agent/claude-rebuild`：Claude Code 从零构建路线（当前分支）
- `agent/claude-continue`：基于已有实现继续演进
- `agent/codex-rebuild`：Codex 从零构建路线

## 技术栈

- Python >= 3.10
- LLM：DeepSeek（OpenAI-compatible API）
- CLI：click
- HTTP：httpx
- 测试：pytest + pytest-asyncio
- 配置：python-dotenv
