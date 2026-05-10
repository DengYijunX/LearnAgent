# LearnAgent — Claude Code 风格 Agent Runtime 设计

## 背景

本设计以 Claude Code 的工程思想为参考：核心价值不在于多个智能体互相对话，而在于一个稳定、可审计、可恢复的 Agent 主循环。模型负责判断下一步，系统负责上下文组装、工具分发、权限拦截、动作执行、状态记录、错误恢复和最终收敛。

当前 LearnAgent 已经具备 Router、ReAct、Plan-Execute、工具层、记忆层和 CLI 控制面，但这些能力分散在不同模块中。`react_agent.py` 直接决定是否搜索并调用工具，`plan_execute_agent.py` 通过 LangGraph 管理复杂任务，工具层虽有 `ToolManager` 抽象但尚未成为 Agent 的唯一执行入口。下一阶段应把这些能力收敛到统一 Agent Runtime。

## 目标

1. 建立统一的 Agent 主循环：想一步、做一步、看结果、再想一步。
2. 将上下文构建、工具执行、权限检查、日志记录从具体 Agent 中剥离。
3. 让 ReAct 和 Plan-Execute 成为同一个 Runtime 下的不同策略，而不是两套孤立流程。
4. 保留 LearnAgent 的学习产品目标：概念学习、项目生成、记忆沉淀、产物写入。
5. 让每轮决策和工具结果都能被 JSONL 日志回放、审计和调试。

## 非目标

1. 不复刻 Claude Code 的全部源码结构。
2. 不在第一阶段实现多 Agent 协作。
3. 不实现插件市场、远程沙箱、IDE 集成。
4. 不让模型绕过工具系统直接执行文件、网络或命令操作。
5. 不把 LangGraph 从项目中移除；它可以作为复杂任务策略或执行图继续存在。

## 总体架构

```text
User Task
  -> Session Init
  -> AgentRuntime.run()
      -> ContextBuilder.build()
      -> LLMClient.decide()
      -> DecisionParser.parse()
      -> StopChecker.check()
      -> ToolRouter.route()
      -> PermissionGate.check()
      -> ToolExecutor.execute()
      -> ObservationStore.append()
      -> StateLogger.log_step()
      -> ContextBuilder.build()
  -> Final Answer / Code Patch / Report
  -> MemoryManager.update()
  -> ArtifactWriter.write()
  -> SessionLogger.close()
```

Agent Runtime 是唯一主循环。它不关心具体工具怎么实现，也不直接读写文件。它只处理四类对象：

- `AgentContext`：本轮给模型看的上下文
- `AgentDecision`：模型输出的结构化决策
- `ToolCall`：模型请求的工具调用
- `Observation`：工具执行后的结果或错误

## 模块边界

### AgentRuntime

路径建议：`src/agent/runtime.py`

职责：

- 管理每个任务的循环生命周期
- 调用 `ContextBuilder` 组装上下文
- 调用 LLM 获取下一步决策
- 将工具调用交给工具系统
- 将 observation 写回历史
- 调用 `StopChecker` 判断是否终止
- 在结束时触发记忆和 artifact 写入

它不负责：

- 不直接执行文件、网络、命令
- 不直接读取项目文件
- 不直接判断权限细节
- 不保存具体记忆格式

### ContextBuilder

路径建议：`src/agent/context_builder.py`

职责：

- 接收用户任务、历史 observation、项目规则、工具 schema、记忆摘要和检索结果
- 输出稳定的 `AgentContext`
- 控制上下文预算，必要时压缩旧 observation
- 根据任务类型选择 prompt：概念学习、项目生成、总结、修复等

上下文来源：

- 用户当前输入
- `plans/` 和 `docs/` 中的规则或设计文档摘要
- `data/memory/index.json` 中的近期学习摘要
- `data/profile.json` 用户画像
- 可用工具定义和权限说明
- 当前任务已产生的 observation

### Tool Registry / Tool Router

路径建议：

- `src/tools/base.py`
- `src/tools/manager.py`
- `src/tools/router.py`

职责：

- 注册所有工具和 schema
- 将模型输出的 tool name 映射到工具实例
- 校验参数
- 统一返回 `ToolResult`

工具必须满足：

- 不直接抛异常给 AgentRuntime
- 失败返回 `ToolResult(ok=False, error=...)`
- metadata 中记录 provider、耗时、截断状态等审计信息
- 高风险工具必须声明风险级别

### PermissionGate

路径建议：`src/tools/permissions.py` 或扩展 `src/registry/permission.py`

职责：

- 在工具执行前判断是否允许
- 根据风险级别返回 `allow`、`deny`、`ask_user`
- 对危险操作附加原因和可读提示

第一阶段策略：

| 风险 | 示例 | 默认行为 |
|---|---|---|
| low | 搜索、读取公开网页、读取记忆摘要 | allow |
| medium | 写 artifact、写 projects 文件 | allow + log |
| high | 删除文件、覆盖重要文件、执行命令、访问内网 URL | deny 或 ask_user |

目前项目暂不实现命令执行工具，因此 high 风险重点是文件覆盖、防路径穿越、SSRF 和密钥泄漏。

### ObservationStore

路径建议：`src/agent/observation.py`

职责：

- 保存每次工具调用的结果
- 区分成功、失败、权限拒绝、用户中止、超预算
- 为下一轮上下文提供压缩后的 observation

建议结构：

```python
class Observation(BaseModel):
    step: int
    tool_name: str | None
    ok: bool
    content: str
    error: str | None = None
    metadata: dict = {}
```

### StateLogger

继续使用并增强：`src/memory/session_logger.py`

职责：

- 每轮写入 JSONL
- 自动脱敏
- 将绝对路径转为相对路径
- 记录 LLM 决策、工具调用、工具结果、错误、final answer

建议事件类型：

- `session_start`
- `context_built`
- `llm_decision`
- `tool_call_requested`
- `permission_checked`
- `tool_result`
- `observation_added`
- `final_answer`
- `session_error`
- `session_end`

### StopChecker

路径建议：`src/agent/stop_checker.py`

职责：

- 防止无限循环
- 明确任务结束条件
- 区分完成、失败、需要用户介入

第一阶段规则：

- 达到 final answer 即停止
- 超过最大轮数停止，默认 8 轮
- 连续工具错误超过 3 次停止
- 权限拒绝后模型再次请求同一高风险工具则停止
- observation 无新增信息时停止

## Agent 决策格式

为了避免模型输出不可控，Runtime 要求模型返回结构化 JSON。

概念学习示例：

```json
{
  "thought": "用户问的是概念解释，需要先搜索资料",
  "action": "tool_call",
  "tool_calls": [
    {
      "name": "web_search",
      "arguments": {
        "query": "RAG retrieval augmented generation",
        "max_results": 5
      }
    }
  ],
  "final_answer": null
}
```

最终回答示例：

```json
{
  "thought": "已有足够资料，可以总结",
  "action": "final_answer",
  "tool_calls": [],
  "final_answer": {
    "topic": "RAG",
    "core_concepts": ["检索增强生成", "Embedding", "向量检索"],
    "learning_points": ["先理解 Embedding", "再理解召回", "最后学习生成增强"],
    "related_techs": ["LangChain", "LlamaIndex"]
  }
}
```

## 与现有模块的关系

### Router

Router 保留，但它只决定任务策略，不直接决定工具执行。

输出建议：

- `simple_learning`
- `project_learning`
- `memory_query`
- `status_command`

### ReAct Agent

`run_react_agent()` 可以降级为兼容入口，内部调用 `AgentRuntime.run(strategy="simple_learning")`。未来不再直接调用 `web_search()` 和 `fetch_content()`。

### Plan-Execute Agent

Plan-Execute 可以作为 `project_learning` 策略。第一阶段保留 LangGraph，但工具执行仍应走 ToolManager。项目文件写入必须经过 PermissionGate 和 path_safety。

### MemoryManager

MemoryManager 不参与主循环决策，只在两个位置使用：

- ContextBuilder 读取近期记忆摘要
- AgentRuntime 完成后写入 learning、profile、artifact 和 session event

## 数据流

### Simple Learning

```text
用户：什么是 RAG
  -> Router: simple_learning
  -> ContextBuilder: 拼用户问题 + 最近记忆 + 工具定义
  -> LLMDecision: 需要 web_search
  -> ToolRouter: web_search
  -> PermissionGate: allow
  -> ToolExecutor: 执行搜索
  -> ObservationStore: 保存搜索摘要
  -> LLMDecision: 需要 content_fetch
  -> ToolExecutor: 抓取正文
  -> ObservationStore: 保存正文摘要
  -> LLMDecision: final_answer
  -> MemoryManager: save_learning + update_profile
  -> ArtifactWriter: write_summary
```

### Project Learning

```text
用户：我要学 FastAPI
  -> Router: project_learning
  -> ContextBuilder: 拼用户目标 + profile + 工具定义
  -> LLMDecision: 生成计划
  -> ObservationStore: 记录 plan
  -> LLMDecision: 写 projects/fastapi/main.py
  -> PermissionGate: medium allow + log
  -> FilesystemTool: path_safety 后写入
  -> ObservationStore: 记录文件路径
  -> StopChecker: 所有步骤完成
  -> MemoryManager: save_learning + log_plan_execute_complete
```

## 错误处理

错误不应直接打断主流程，除非触发停止条件。

| 错误 | Runtime 行为 |
|---|---|
| LLM 输出 JSON 解析失败 | 写 observation，要求模型重试一次 |
| 工具不存在 | 写 observation，提示可用工具 |
| 权限拒绝 | 写 observation，不执行工具 |
| 工具执行异常 | 转成 ToolResult failure |
| 记忆写入失败 | warning + 继续返回最终答案 |
| artifact 写入失败 | warning + 最终答案中提示保存失败 |
| 连续错误过多 | 停止并返回失败报告 |

## 安全约束

1. 所有文件写入必须走 `safe_path()`。
2. `filesystem` 只能写 `projects/`。
3. `artifact_writer` 只能写 `artifacts/`。
4. `content_fetch` 只允许 `http/https`，禁止 localhost、内网 IP、file scheme。
5. SessionLogger 必须递归脱敏字段和值。
6. 工具日志只记录 metadata，不记录完整网页正文、完整代码或密钥。
7. PermissionGate 必须在 ToolExecutor 前执行。

## 日志格式

建议每轮 JSONL 记录包含：

```json
{
  "time": "2026-05-11T10:00:00",
  "session_id": "20260511-cli-001",
  "step": 3,
  "type": "tool_result",
  "tool": "web_search",
  "ok": true,
  "metadata": {
    "provider": "tavily",
    "result_count": 5,
    "truncated": true
  }
}
```

## 推荐文件结构

```text
src/agent/
├── runtime.py
├── context_builder.py
├── decision.py
├── observation.py
├── stop_checker.py
├── strategies.py
├── react_agent.py              # 兼容入口，内部调用 runtime
└── plan_execute_agent.py       # 兼容入口，逐步迁移到 runtime

src/tools/
├── base.py
├── manager.py
├── router.py
├── permissions.py
├── web_search.py
├── content_fetch.py
├── github_disco.py
├── filesystem.py
└── artifact_writer.py

src/core/
├── prompt_registry.py
└── prompts/
    ├── runtime_simple_learning.md
    ├── runtime_project_learning.md
    ├── router.md
    └── summarize.md
```

## 分阶段迁移

### Phase 1：Runtime MVP

- 新增 `AgentRuntime`
- 新增 `ContextBuilder`
- 新增 `AgentDecision` / `ToolCall` / `Observation`
- 实现最多 8 轮的简单主循环
- 先支持 `web_search`、`content_fetch`、`artifact_writer`
- `run_react_agent()` 改为兼容包装

验收：

- simple 学习任务可以通过 Runtime 完成
- 每轮写 JSONL
- 工具调用走 ToolManager
- 现有测试保持通过

### Phase 2：权限与安全统一

- 完善 PermissionGate
- filesystem 接入 path_safety
- content_fetch 接入 SSRF 防护
- session_logger 递归脱敏和路径相对化

验收：

- 路径穿越被拒绝
- localhost / file URL 被拒绝
- 日志不暴露密钥和本机绝对路径

### Phase 3：Project Learning 迁移

- Plan-Execute 通过 Runtime 发起文件写入工具
- 修复项目目录不一致问题
- generated_files 记录所有步骤文件，而不是只记录第一步

验收：

- 复杂任务生成项目文件目录一致
- plan_execute_complete 记录完整文件列表
- 失败不影响最终学习总结返回

### Phase 4：上下文压缩与恢复

- ObservationStore 支持摘要化旧步骤
- SessionLogger 支持从 JSONL 恢复最近状态
- StopChecker 增加无进展检测

验收：

- 长任务不会无限增长上下文
- 工具失败后能生成清晰失败报告

## 测试策略

单元测试：

- `ContextBuilder` 是否包含任务、工具定义、近期记忆
- `AgentDecision` 是否能解析 final answer 和 tool call
- `PermissionGate` 是否拦截高风险工具
- `StopChecker` 是否按轮数和连续错误停止
- `SessionLogger` 是否脱敏和相对化路径

集成测试：

- Mock LLM 输出 tool call，Runtime 执行工具并追加 observation
- Mock LLM 输出 final answer，Runtime 停止并写记忆
- 工具失败后 Runtime 继续一轮并最终返回错误报告

回归测试：

- 原有 `/learn` simple 接口输出不变
- CLI `/history`、`/profile`、`/memory` 不退化
- `make lint` 和 `make test` 通过

## 设计取舍

### 为什么先做单 Agent Runtime

当前项目的主要问题不是智能体数量不足，而是执行边界不够统一。先统一主循环可以解决工具绕行、权限分散、日志不完整、状态难恢复等基础问题。多 Agent 可以以后作为 Runtime 的上层策略，而不是现在引入复杂度。

### 为什么保留 Router

Router 是产品层的任务分类入口，仍然有价值。但它不应拥有工具执行权。它只选择策略，真正的行动由 Runtime 管理。

### 为什么不马上删除 LangGraph

LangGraph 对复杂教学项目仍有价值，尤其是计划、执行、总结等阶段性流程。迁移目标不是删除它，而是让 LangGraph 节点内部也遵守统一工具和权限边界。

## 成功标准

1. Agent 的所有工具调用都能在日志中看到请求、权限判断、执行结果。
2. 文件、网络、artifact 写入都不能绕过权限和安全检查。
3. ReAct 和 Plan-Execute 能共享同一套 Context、Tool、Permission、Logger。
4. 用户得到的最终回答不因记忆或 artifact 写入失败而中断。
5. 出错时能通过 JSONL 定位是哪一步、哪个工具、什么输入导致失败。
