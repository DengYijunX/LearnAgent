<p align="center">
  <h1 align="center">LearnAgent</h1>
  <p align="center">面向自学者的 AI 学习助手 —— 发现 · 理解 · 实践 · 复盘</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python">
  <img src="https://img.shields.io/badge/tests-135-green" alt="Tests">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License">
</p>

---

## 这是什么

LearnAgent 不是 ChatBot。它是一个**学习任务执行系统**——能主动搜索资料、阅读文档、分析仓库、创建示例项目、运行代码，并跟踪你的学习进度。

想学一个新技术？告诉 LearnAgent，它会帮你完成整个学习流程，而不是只丢给你几段文字。

```
> 我想学习 Flask

  意图: learn_concept · 主题: flask

  📁 新主题：flask
  📂 workspace: storage/workspace/flask

  ✅ 找到 5 条搜索结果 (3.6s)
     · Flask 入门教程 | 菜鸟教程
     · Welcome to Flask — Flask Documentation
     · Flask Tutorial - GeeksforGeeks

  ✅ 读取网页，4530 字符 (3.4s)

  ✅ 写入文件 learn_flask.py (0.1s)

  ✅ 执行完毕 (exit=0)，输出 156 字符 (2.1s)

  ── 搜索 ×3 · 阅读 ×2 · 创建文件 ×1 · 运行代码 ×2  |  ⏱ 38s
```

---

## 快速开始

```bash
# 1. 克隆并安装
git clone git@github.com:DengYijunX/LearnAgent.git && cd LearnAgent && pip install -e .

# 2. 配置 API key
cp .env.example .env   # 编辑 .env，填写 DEEPSEEK_API_KEY

# 3. 运行
python -m app.main --real
```

更多配置：`.env.example` | MCP 工具：`.mcp.example.json` | 冒烟测试：`python scripts/smoke_llm_real.py`

---

## 核心能力

**自动学习流程：** LLM Router 识别意图 → Skill 注入工作流 → Agent Loop 驱动工具调用

| 我能做什么 | 示例 |
|---|---|
| 学习新技术 | "我想学习 Rust 的 async/await" → 搜索 + 读文档 + 写示例 + 运行 |
| 分析 GitHub 仓库 | "https://github.com/huggingface/smolagents 分析这个项目" |
| 动手写代码 | 在隔离 workspace 中创建文件、运行 Python，结果实时展示 |
| 生成学习计划 | 拆解核心概念 → 分层递进路线 → 练习任务 |
| 复盘进度 | "复盘一下最近学的 Agent 架构" |
| 恢复上次会话 | `python -m app.main --real --resume latest` |

**8 个内置工具：** 搜索(DuckDuckGo) · 网页读取(BeautifulSoup4) · GitHub 分析 · 文件读写 · 代码执行(Docker Sandbox 可选) · 项目文件浏览 · 学习任务管理 · MCP 外部工具

**CLI 命令：** `/help` `/plan` `/topic` `/progress` `/sessions` `/memory` `/tools` `/status` `/clear`

---

## 运行测试

```bash
pytest tests/ -v                   # 135 个单元测试 (mock，无需网络)
RUN_REAL_TESTS=1 pytest tests/ -v  # 真实集成测试 (需要 API key)
python scripts/sandbox_test.py --real  # 自动化端到端测试
```

---

## 架构

```
app/
├── main.py                    # CLI 入口
├── config/settings.py         # .env 配置
├── llm/                       # LLM 层
│   ├── base.py                #   LLMClient 抽象
│   ├── deepseek_client.py     #   DeepSeek (OpenAI-compatible)
│   ├── mock_client.py         #   Mock 实现（测试用）
│   └── model_selector.py      #   模型路由
├── tools/                     # 工具层
│   ├── base.py / registry.py  #   Tool 接口 + ToolRegistry
│   ├── search_web.py          #   DuckDuckGo 搜索
│   ├── read_url.py            #   网页读取 (BS4)
│   ├── github_analyzer.py     #   仓库分析 (免 token)
│   ├── workspace_tools.py     #   文件读写 + 代码执行 + Sandbox
│   └── todo_tools.py          #   学习任务管理
├── core/                      # 编排层
│   ├── agent_loop.py          #   Agent 循环 + 事件回调
│   ├── query_engine.py        #   会话编排 + Skill/Topic 管理
│   ├── llm_router.py          #   LLM 意图分类
│   └── router.py              #   正则路由（降级）
├── context/                   # 上下文层
│   ├── context_builder.py     #   三段式 System Prompt
│   └── compaction.py          #   Token Budget 压缩
├── memory/                    # 持久化层
│   ├── session_store.py       #   JSONL 会话存储
│   └── memory_store.py        #   Markdown 长期记忆
├── safety/                    # 安全层
│   └── permission.py          #   权限分级
├── skills/                    # Skill 系统
│   └── loader.py              #   SKILL.md 加载
└── mcp/                       # MCP 外部工具
    ├── client.py              #   JSON-RPC 2.0 客户端
    ├── adapter.py             #   MCP → Tool 适配
    └── loader.py              #   .mcp.json 配置
```

---

## 技术栈

`Python 3.10+` `asyncio` `httpx` `BeautifulSoup4` `ddgs` `pytest` `Docker` `DeepSeek API` `JSON-RPC 2.0`

---

## 项目状态

当前分支 `agent/claude-rebuild` — Claude Code 从零构建路线。

| 阶段 | 内容 |
|---|---|
| Phase 1 | Agent 骨架、8 工具、LLM 双实现、Router、3 Skill、持久化、CLI |
| Phase 2 | Plan Mode、Token Budget、Docker Sandbox、BS4 ReadUrl、命令过滤 |
| Phase 3 | MCP 客户端（JSON-RPC + Tool Adapter） |
| 体验 | 进度展示、信任窗口、粘贴合并、Ctrl+C 确认、topic 管理、会话恢复 |
| 测试 | 135 用例覆盖全部核心模块 |

---

## License

MIT
