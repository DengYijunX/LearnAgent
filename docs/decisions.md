# 架构决策记录

## Decision 001：第一阶段采用 CLI First

日期：2026-05-20

状态：Accepted

背景：

第一阶段需要先验证 LearnAgent 的核心运行时，不应过早引入 HTTP API 或前端复杂度。

决策：

构建 Python CLI first 的最小可运行版本。FastAPI、Flask 和前端工作后置。

理由：

CLI 能让初始闭环保持足够小，也更容易验证 Router、Tool Layer、LLM Client、Workflow、Memory 和测试。后续 API 入口应复用同一套核心 workflow。

影响：

CLI 必须保持轻量。核心 Agent 逻辑应放在 CLI 入口之外，方便后续 API 复用。

## Decision 002：DeepSeek 通过 OpenAI-Compatible API 接入

日期：2026-05-20

状态：Accepted

背景：

LearnAgent 需要尽早接入真实 LLM，同时保留后续切换服务商的能力。

决策：

第一阶段使用 DeepSeek 作为主要 LLM 服务商，并通过 OpenAI-compatible API 接入。提供 `MockLLMClient` 和 `DeepSeekLLMClient` 两种实现。

理由：

OpenAI-compatible adapter 可以让 workflow 代码不依赖具体服务商细节。单元测试使用 mock client，smoke script 用于验证真实 DeepSeek 接入。

影响：

业务代码只能通过 LLM client 抽象调用模型，不能直接调用 HTTP API。

## Decision 003：模型 ID 必须来自配置

日期：2026-05-20

状态：Accepted

背景：

DeepSeek V4 Flash 和 DeepSeek V4 Pro 的 model ID 必须以实际服务平台提供的名称为准。

决策：

模型名保存在 `.env` 和 config 模块中。`.env.example` 提供 `DEEPSEEK_SMALL_MODEL` 和 `DEEPSEEK_LARGE_MODEL` 配置项。

理由：

不同平台的模型 ID 可能变化。如果在 workflow、tools 或 agent loop 中硬编码，会增加后续修改风险。

影响：

Workflow 和 tools 应按任务或模式请求模型选择，而不是直接依赖具体模型字符串。

## Decision 004：第一阶段实现简单 ModelSelector

日期：2026-05-20

状态：Accepted

背景：

LearnAgent 需要支持 small model 和 large model 的简单路由，但不需要复杂多模型编排。

决策：

实现简单规则型 ModelSelector。`normal`、`summary`、`lightweight` 使用 small model；`deep`、`planning`、`repo_analysis` 使用 large model。

理由：

这能满足已确认的 DeepSeek 策略，同时保持第一阶段实现简单、可测试。

影响：

Workflow 应依赖 ModelSelector，而不是内嵌服务商模型名。

## Decision 005：第一阶段使用 Mock Web Search 和 Mock GitHub Analyzer

日期：2026-05-20

状态：Accepted

背景：

搜索和 GitHub 分析很重要，但真实外部接入会带来服务商选择、凭据、限流、解析质量和 token 预算等问题。

决策：

第一阶段定义可替换的 tool 接口和 mock 实现。真实 Web Search 和 GitHub API 接入后置。

理由：

这样可以先验证系统架构，不会过早绑定搜索 API 或 GitHub 凭据。

影响：

Workflow 必须依赖 Tool 接口和 ToolRegistry，而不是具体 mock 类。真实实现应在后续确认后再加入。

## Decision 006：本地 Session 和 Memory 存储

日期：2026-05-20

状态：Accepted

背景：

LearnAgent 需要本地 debug trace 和长期学习记忆，但第一阶段不应引入数据库。

决策：

Session 和 workflow trace 使用 JSONL；长期 memory 使用 Markdown + frontmatter。本地数据存放在 `storage/sessions/`、`storage/runs/` 和 `storage/memory/`。

理由：

JSONL 适合追加写入，也便于调试。Markdown memory 可读、可编辑，适合人工检查。

影响：

`storage/` 由 Git 忽略。用户学习记录、run trace、LLM 响应和本地 memory 文件不得提交。

## Decision 009：第一阶段 Todo 使用本地 JSON

日期：2026-05-20

状态：Accepted

背景：

LearnAgent 需要维护当前学习步骤，但第一阶段不引入数据库或复杂 Task Graph。

决策：

使用 `storage/tasks/` 下的 JSON 文件保存当前 session 的 learning todo。通过 `LearningTodoWriteTool` 暴露写入能力。

理由：

JSON 易读、易测试，也方便后续替换为 SQLite 或更完整的 Task Graph。

影响：

`storage/tasks/` 由 Git 忽略。Workflow 和 Agent Loop 应通过 ToolRegistry 使用 todo 工具，不直接依赖底层文件结构。

## Decision 010：第一阶段工具调用后暂停继续暴露工具

日期：2026-05-21

状态：Accepted

背景：

真实 DeepSeek Agent smoke test 中，模型在工具调用后可能继续重复调用工具，导致达到 `max_turns` 仍没有最终文本输出。

决策：

第一阶段 Agent Loop 在执行一轮工具后，下一次 LLM 请求不再继续传入工具列表，而是让模型基于 observation 生成最终回答。

理由：

这能稳定验证“真实 LLM + mock tools”的最小闭环，避免第一阶段陷入复杂多轮工具调度问题。

影响：

第一阶段优先保证单轮工具使用后的最终回答。后续如果要支持复杂多轮工具规划，需要单独设计工具预算、重复调用保护和更明确的 planner/executor 策略。

## Decision 007：测试边界

日期：2026-05-20

状态：Accepted

背景：

项目需要可靠测试，同时避免意外调用真实 API。

决策：

使用 pytest。单元测试默认使用 mock LLM 和 mock tools。真实集成测试与 smoke script 只有在显式设置 `RUN_REAL_TESTS=1` 且必要凭据存在时才运行。

理由：

这样可以让常规测试保持快速、确定，并避免 API 成本。

影响：

LLM client 实现后，应通过 `scripts/smoke_llm_real.py` 验证真实 LLM 接入。

## Decision 008：Tool Calling 的 JSON Action Fallback

日期：2026-05-20

状态：Accepted

背景：

DeepSeek 的 tool calling 行为可能随模型版本和 API 形态不同而变化。

决策：

第一阶段可以支持 JSON action 输出，作为标准 tool calling 的 fallback。

理由：

即使原生 tool calling 不稳定，JSON action fallback 也能让 agent loop 验证工具选择流程。

影响：

工具调用格式差异应隔离在 LLM client 或 agent loop 边界中，不应扩散到业务 workflow 代码里。
