# LearnAgent 未确认细节处理规则

## 1. 文档目的

在 LearnAgent 项目构建过程中，设计文档可能不会覆盖所有工程细节。

为了避免 Claude Code / Codex / 其他 Agent 在未确认的情况下擅自做出影响项目路线的决定，本规则用于约束 Agent 在遇到未明确说明的问题时如何处理。

核心原则：

> 小问题可以按默认方案推进，但关键技术路线必须先询问确认。

本规则适用于以下实验路线：

```text
agent/claude-continue
agent/claude-rebuild
agent/codex-rebuild
```

也适用于后续新增的其他 Agent 实验分支。

---

## 2. 总体处理原则

当 Agent 遇到设计文档没有明确说明的工程细节时，不应直接硬编码或大规模实现，而应先进行判断。

处理方式分为三类：

```text
A 类：必须询问确认后再执行
B 类：可以采用推荐默认方案，但必须记录
C 类：可以自行决定
```

判断标准：

- 如果会影响项目长期架构、技术路线、依赖选择、部署方式，属于 A 类。
- 如果不会阻塞项目推进，但会影响后续维护和规范，属于 B 类。
- 如果只是局部实现细节，不影响整体路线，属于 C 类。

---

## 3. A 类问题：必须询问确认

A 类问题会影响项目整体架构、长期维护成本或技术路线，必须先询问用户确认，不得擅自执行。

### 3.1 LLM 相关

以下问题必须确认：

- 使用哪个 LLM 作为 Agent 基座
- 使用哪个 API 服务商
- 是否使用 OpenAI-compatible API
- 是否支持多模型切换
- 是否引入 embedding 模型
- 是否引入 reranker 模型
- 是否接入真实联网搜索能力
- 是否允许调用外部付费 API
- 是否需要支持本地模型服务
- 是否需要区分规划模型、执行模型、总结模型

示例：

```text
是否默认使用 SiliconFlow + Qwen/Qwen2.5-7B-Instruct 作为 LLM 基座？
```

这类问题会影响配置文件、LLM Client、依赖、测试 mock 和后续扩展方式，因此必须确认。

---

### 3.2 项目形态相关

以下问题必须确认：

- 先做 CLI、FastAPI、Flask，还是 Web 全栈
- 是否直接引入前端
- 是否将项目拆分为前后端
- 是否改变项目整体目录结构
- 是否引入大型框架或复杂依赖
- 是否从单体应用改为多服务结构
- 是否引入异步任务系统
- 是否需要 Docker 化

示例：

```text
项目第一阶段是先做 CLI 原型，还是直接做 FastAPI 后端？
```

---

### 3.3 架构相关

以下问题必须确认：

- 是否改变 Router / Tool / Memory / Workflow 的分层方式
- 是否引入多 Agent 编排
- 是否引入 Planner / Executor / Critic 等复杂结构
- 是否引入异步任务队列
- 是否引入数据库
- 是否引入知识图谱
- 是否引入 RAG / VectorStore
- 是否重构大量已有代码
- 是否删除现有重要文件
- 是否把多个模块合并为单一大模块
- 是否改变核心数据流

示例：

```text
是否将当前单 Agent 架构升级为 Planner-Executor 多 Agent 架构？
```

---

### 3.4 外部服务相关

以下问题必须确认：

- 是否使用 GitHub API
- 是否使用搜索 API
- 是否使用数据库服务
- 是否使用云端存储
- 是否使用第三方托管平台
- 是否使用浏览器自动化工具
- 是否使用外部爬虫服务
- 是否接入用户账号系统
- 是否存储用户隐私信息

示例：

```text
GitHub 仓库分析工具是先使用 GitHub API，还是先基于公开页面 / README 抓取？
```

---

### 3.5 安全与隐私相关

以下问题必须确认：

- 是否保存用户输入历史
- 是否保存 LLM 原始响应
- 是否保存 API 请求日志
- 是否保存工具执行 trace
- 是否上传用户数据到第三方服务
- 是否在日志中记录 URL、token、email 等敏感信息
- 是否允许 Agent 自动执行 shell 命令
- 是否允许 Agent 自动修改 Git 历史

示例：

```text
是否需要保存完整 workflow trace？保存时是否包含用户原始输入？
```

---

## 4. B 类问题：可以默认处理，但必须记录

B 类问题不会阻塞项目推进，但会影响后续维护、规范和扩展。Agent 可以采用推荐默认方案先推进，但必须记录到：

```text
docs/decisions.md
```

---

### 4.1 配置类

以下问题属于 B 类：

- 配置文件命名
- `.env.example` 字段设计
- 默认 temperature
- 默认 max_tokens
- 默认日志级别
- 默认输出目录
- 默认运行环境名称
- 默认超时时间
- 默认重试次数

示例：

```text
默认 temperature 设置为 0.2，并记录到 docs/decisions.md。
```

---

### 4.2 存储类

以下问题属于 B 类：

- 初期 memory 使用 JSON、Markdown 还是 SQLite
- 日志保存在 `logs/` 还是 `storage/runs/`
- workflow trace 是否保存为 JSON
- 用户学习记录的本地文件结构
- 是否按日期创建运行记录
- 是否为每次执行生成 run_id
- 是否拆分 short-term memory 和 long-term memory

示例：

```text
初期 memory 使用本地 JSON 文件保存，后续预留 SQLite 扩展。
```

---

### 4.3 代码组织类

以下问题属于 B 类：

- 测试目录结构
- schema 文件位置
- tool registry 文件位置
- config 模块位置
- 异常类文件位置
- prompt 模板文件位置
- CLI 入口文件位置
- mock 文件位置
- 示例文件位置

示例：

```text
将工具注册逻辑放在 app/tools/registry.py。
```

---

### 4.4 输出格式类

以下问题属于 B 类：

- 学习总结字段
- 技术图谱字段
- 实践任务字段
- workflow 返回 schema
- error response 格式
- CLI 输出格式
- JSON 输出字段命名
- 日志字段命名

示例：

```text
学习结果默认包含 summary、concepts、learning_path、practice_tasks、related_topics。
```

---

### 4.5 测试规范类

以下问题属于 B 类：

- pytest 测试目录
- mock LLM 的方式
- mock web search 的方式
- 是否要求每个核心模块都有基础测试
- 是否加入最小 CI 配置
- 是否使用 coverage

示例：

```text
Router 和 Workflow 必须有基础单元测试。
```

---

## 5. C 类问题：可以自行决定

C 类问题属于低风险实现细节，Agent 可以自行决定，但仍应保持代码清晰、可维护。

以下问题属于 C 类：

- 函数命名
- 变量命名
- 小型工具函数拆分
- README 文案调整
- 基础异常处理
- 简单测试样例
- 类型注解
- docstring
- 代码格式化
- 小范围重构
- 局部 import 顺序
- 简单 helper 函数放置位置
- 简单命令行提示文本

要求：

- 不得因为 C 类问题改变整体架构。
- 不得把 C 类小问题扩大成大规模重构。
- 不得为了局部命名调整删除已有重要逻辑。

---

## 6. 默认技术偏好

如果用户没有另外说明，LearnAgent 初期默认采用以下方案。

---

### 6.1 LLM 调用

默认方案：

```text
LLM 服务商：SiliconFlow
LLM 接口：OpenAI-compatible API
默认聊天模型：Qwen/Qwen2.5-7B-Instruct
备用模型：Qwen/Qwen3-8B
```

要求：

- 使用 OpenAI-compatible API 封装
- 预留切换模型能力
- 不允许把模型名硬编码在业务逻辑中
- 不允许硬编码 API key
- 业务代码不得直接散落调用 requests.post
- 应通过统一 LLMClient 调用模型

推荐配置项：

```env
SILICONFLOW_API_KEY=
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SF_CHAT_MODEL=Qwen/Qwen2.5-7B-Instruct
SF_CHAT_TEMPERATURE=0.2
SF_CHAT_MAX_TOKENS=2048
```

---

### 6.2 配置管理

默认方案：

- API key 放在 `.env`
- base_url、model_name、temperature 等通过配置模块读取
- 提供 `.env.example`
- 业务代码不直接读取环境变量
- 统一通过 config 模块获取配置
- 本地 `.env` 不提交到 Git
- `.env.example` 可以提交

推荐结构：

```text
app/
  config/
    __init__.py
    settings.py
.env.example
```

---

### 6.3 项目形态

默认方案：

- 初期优先实现 Python CLI 最小可运行版本
- 后续再扩展 FastAPI 后端
- 不急于做复杂前端
- 优先保证核心 Agent 流程可运行
- CLI 应便于本地调试和后续接入后端

第一阶段目标：

```text
用户输入技术名词 / 链接 / GitHub 仓库地址
→ Router 判断输入类型
→ Workflow 选择处理流程
→ Tool 获取必要信息
→ LLM 生成结构化学习结果
→ Memory 记录本次学习结果
```

---

### 6.4 Memory

默认方案：

- 初期使用本地 JSON / Markdown
- 暂不直接引入数据库
- 记录用户查询历史、学习主题和生成结果
- 保存 workflow 执行摘要
- 后续可扩展为 SQLite / 向量数据库

推荐结构：

```text
storage/
  memory/
    sessions.json
    topics.json
  runs/
    run_YYYYMMDD_HHMMSS.json
```

---

### 6.5 Tool Layer

默认方案：

- Web search、Web fetch、GitHub repo analyzer、LLM client 都应通过工具层抽象
- 工具应支持统一注册
- 工具失败时应返回结构化错误
- 不建议业务 workflow 直接调用底层 API
- 初期可以 mock 部分外部工具
- 外部服务接入应可替换

推荐工具接口：

```text
Tool
├── name
├── description
├── input_schema
├── run(input)
└── output / error
```

推荐工具：

```text
web_fetch
web_search
github_repo_analyzer
llm_summarizer
memory_reader
memory_writer
```

---

### 6.6 Workflow

默认方案：

- Router 负责判断输入类型
- Workflow 负责组织工具调用
- Tool 负责单一能力执行
- LLM Client 负责模型调用
- Memory 负责记录和读取上下文
- Output Schema 负责统一输出结构

推荐数据流：

```text
User Input
→ Router
→ Workflow
→ Tool Registry
→ Tools
→ LLM Client
→ Output Schema
→ Memory
→ Final Response
```

---

### 6.7 Testing

默认方案：

- 使用 pytest
- Router 必须有测试
- Workflow 至少有 mock 测试
- LLM Client 使用 mock，不在单元测试中真实调用 API
- Tool Registry 必须测试注册和查找
- Memory 必须测试读写

推荐测试结构：

```text
tests/
  test_router.py
  test_workflow.py
  test_tool_registry.py
  test_memory.py
  test_llm_client.py
```

---

## 7. Agent 遇到未确认问题时的输出格式

当 Agent 遇到需要确认的问题时，应按照以下格式输出。

```markdown
## 待确认问题

### 问题 1：是否使用 SiliconFlow 作为默认 LLM 服务商？

类别：

A 类，必须确认。

可选方案：

1. SiliconFlow + OpenAI-compatible API
2. OpenAI API
3. 本地模型服务
4. 先 mock LLM Client

推荐方案：

使用 SiliconFlow + OpenAI-compatible API。

推荐理由：

1. 与项目已有偏好一致
2. 便于切换 Qwen 系列模型
3. 成本和接入复杂度较低
4. 后续可以兼容其他 OpenAI-compatible 服务

是否需要等待确认：

需要。该选择会影响 LLM Client、配置文件、依赖设计和测试方案。
```

---

## 8. 决策记录要求

凡是 B 类及以上问题，都应记录到：

```text
docs/decisions.md
```

如果 `docs/decisions.md` 不存在，应创建该文件。

记录格式如下：

```markdown
# 架构决策记录

## Decision 001：LLM Client 使用 OpenAI-compatible API

日期：YYYY-MM-DD

状态：Accepted

背景：

项目需要调用外部 LLM 作为 Agent 基座，同时希望后续可以切换模型服务商。

决策：

使用 OpenAI-compatible API 作为统一 LLM 调用接口。

理由：

1. 兼容 SiliconFlow、OpenAI 等服务
2. 便于模型切换
3. 降低业务代码和具体服务商的耦合

影响：

1. 需要 `.env.example`
2. 需要统一 config 模块
3. 需要封装 LLMClient
4. 业务代码不能直接调用 requests.post
```

---

## 9. 禁止行为

Agent 不允许执行以下行为：

1. 未确认就切换分支
2. 未确认就修改 main
3. 未确认就删除大量文件
4. 未确认就引入大型框架
5. 未确认就硬编码 API key
6. 未确认就改变项目主架构
7. 未确认就将 CLI 改成完整 Web 项目
8. 未确认就引入数据库、队列、云服务
9. 未确认就把所有逻辑写进一个巨大文件
10. 未确认就忽略设计文档重新设计项目
11. 未确认就调用真实付费 API
12. 未确认就把 `.env` 提交到 Git
13. 未确认就把日志中写入敏感信息
14. 未确认就重写 Git 历史
15. 未确认就合并其他实验分支代码

---

## 10. 推荐执行流程

正式写代码前，Agent 应先完成以下步骤：

1. 阅读项目设计文档
2. 阅读本规则
3. 总结项目目标
4. 列出待确认问题
5. 给出推荐默认方案
6. 标明哪些问题必须等待确认
7. 标明哪些问题可以先按默认方案推进
8. 生成第一阶段实施计划
9. 等待用户确认后再开始编码

---

## 11. 对不同实验路线的要求

### 11.1 agent/claude-continue

该路线是基于已有代码继续演进。

要求：

- 不要从零重写
- 不要直接推翻已有实现
- 先分析当前项目结构
- 再提出渐进式改造计划
- 保持项目尽量可运行
- 每个阶段提交一次 commit

---

### 11.2 agent/claude-rebuild

该路线是 Claude Code 从零构建路线。

要求：

- 当前项目只以设计文档作为输入
- 不参考 `agent/claude-continue` 的已有实现
- 从目录结构开始重新设计
- 优先实现最小可运行版本
- 先做 CLI 原型，再考虑 FastAPI
- 保持代码模块化，便于和 Codex 路线对比

---

### 11.3 agent/codex-rebuild

该路线是 Codex 从零构建路线。

要求：

- 当前项目只以设计文档作为输入
- 不参考其他实验分支实现
- 从零搭建工程骨架
- 优先实现 P0 按需对话学习能力
- 保持代码模块化，便于和 Claude 路线对比
- 每个阶段提交一次 commit

---

## 12. 当前项目默认结论

若用户未进一步修改，当前默认结论如下：

```text
LLM 服务商：SiliconFlow
LLM 接口：OpenAI-compatible API
默认模型：Qwen/Qwen2.5-7B-Instruct
备用模型：Qwen/Qwen3-8B
项目形态：Python CLI first
后端扩展：后续 FastAPI
Memory：本地 JSON / Markdown
工具层：Tool Registry
配置：.env + config 模块
测试：pytest
文档：README + docs/decisions.md
日志：storage/runs/ 或 logs/
分支策略：main 稳定，agent/* 作为实验路线
```

---

## 13. 初始提示词建议

### 13.1 Claude 从零构建路线

适用于：

```text
本地目录：LearnAgent-Claude
分支：agent/claude-rebuild
```

提示词：

```text
你当前工作目录是 LearnAgent-Claude，当前分支是 agent/claude-rebuild。这是一个从零开始构建 LearnAgent 的实验路线。

请先阅读：
1. docs/agent-design-reference.md
2. docs/learnagent-architecture.md
3. docs/decision-confirmation-rules.md

暂时不要写代码。

请先完成以下任务：
1. 总结你对 LearnAgent 项目目标的理解
2. 总结你理解的核心架构分层
3. 列出所有需要我确认的关键工程细节
4. 对每个问题给出可选方案
5. 给出你的推荐默认方案
6. 说明推荐理由
7. 标明该问题属于 A 类、B 类还是 C 类
8. 标明哪些问题必须等待我确认，哪些可以先按默认方案推进

在我确认前，不要创建项目代码，不要引入依赖，不要切换分支。
```

---

### 13.2 Codex 从零构建路线

适用于：

```text
本地目录：LearnAgent-Codex
分支：agent/codex-rebuild
```

提示词：

```text
你当前工作目录是 LearnAgent-Codex，当前分支是 agent/codex-rebuild。这是一个从零开始构建 LearnAgent 的实验路线。

请先阅读：
1. docs/agent-design-reference.md
2. docs/learnagent-architecture.md
3. docs/decision-confirmation-rules.md

暂时不要写代码。

请先完成以下任务：
1. 总结你对 LearnAgent 项目目标的理解
2. 总结你理解的核心架构分层
3. 列出所有需要我确认的关键工程细节
4. 对每个问题给出可选方案
5. 给出你的推荐默认方案
6. 说明推荐理由
7. 标明该问题属于 A 类、B 类还是 C 类
8. 标明哪些问题必须等待我确认，哪些可以先按默认方案推进

在我确认前，不要创建项目代码，不要引入依赖，不要切换分支。
```

---

### 13.3 Claude 继续构建路线

适用于：

```text
本地目录：LearnAgent-work
分支：agent/claude-continue
```

提示词：

```text
你当前工作目录是 LearnAgent-work，当前分支是 agent/claude-continue。这是一个基于已有实现继续演进 LearnAgent 的实验路线。

请先阅读：
1. docs/agent-design-reference.md
2. docs/learnagent-architecture.md
3. docs/decision-confirmation-rules.md

暂时不要写代码。

请先完成以下任务：
1. 分析当前项目结构和已有实现
2. 总结当前代码与设计文档之间的差距
3. 列出所有需要我确认的关键工程细节
4. 对每个问题给出可选方案
5. 给出你的推荐默认方案
6. 说明推荐理由
7. 标明该问题属于 A 类、B 类还是 C 类
8. 标明哪些问题必须等待我确认，哪些可以先按默认方案推进

在我确认前，不要大规模重构，不要删除已有重要代码，不要引入大型依赖，不要切换分支。
```

---

## 14. 后续编码前的确认模板

当 Agent 输出待确认问题后，用户可以使用以下格式回复：

```markdown
## 确认结果

### A 类问题确认

1. LLM 服务商：确认使用 SiliconFlow
2. LLM 接口：确认使用 OpenAI-compatible API
3. 默认模型：确认使用 Qwen/Qwen2.5-7B-Instruct
4. 项目形态：确认第一阶段先做 Python CLI
5. 后端框架：暂不引入 FastAPI，后续再说
6. Memory：确认初期使用 JSON / Markdown
7. Web Search：第一阶段先做抽象接口和 mock，不接真实搜索 API
8. GitHub Analyzer：第一阶段先分析 README / repo URL，后续再接 GitHub API

### B 类问题处理

B 类问题可以按推荐默认方案推进，但必须记录到 docs/decisions.md。

### 编码许可

现在可以开始第一阶段实现：

1. 创建项目目录结构
2. 创建配置模块
3. 创建 Router
4. 创建 Tool Registry
5. 创建 mock LLM Client
6. 创建最小 Workflow
7. 创建 CLI 入口
8. 创建基础测试

每完成一个明确阶段，请进行一次 git commit。
```

---

## 15. 文档维护要求

本规则不是一次性文档。

当项目进入新阶段时，应根据实际情况更新本文件。

可能需要更新的情况：

- 项目从 CLI 扩展到 FastAPI
- 接入真实 LLM API
- 接入真实 Web Search API
- 接入 GitHub API
- 引入数据库
- 引入 RAG
- 引入多 Agent 编排
- 引入前端
- 引入部署流程
- 引入用户系统

更新原则：

- 新增规则应尽量明确
- 不要把所有小问题都升级为 A 类
- 保持 Agent 可以推进低风险任务
- 对高风险架构决策保持确认机制

---

## 16. 总结

本规则的目标不是限制 Agent 工作，而是让 Agent 在正确边界内工作。

最终目标：

```text
低风险细节：Agent 自主推进
中风险规范：Agent 默认推进并记录
高风险决策：Agent 先问用户确认
```

这样可以在保证开发效率的同时，避免项目路线失控。
