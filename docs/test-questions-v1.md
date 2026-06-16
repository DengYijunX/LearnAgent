# LearnAgent 第一阶段闭环测试问题集

## 测试层级说明

- **L0**：纯 mock，不依赖网络，当前即可运行
- **L1**：需要接入真实 LLM（DeepSeek API key）
- **L2**：需要接入真实搜索/网页读取
- **L3**：需要接入 GitHub API 或真实仓库读取

---

## L0 测试：纯 Mock 模式（当前即可验证）

这些测试验证架构骨架是否通畅，无需任何外部 API。

### L0-1：CLI 启动与退出

**输入：**
```
/help
/clear
/exit
```

**预期：**
- `/help` 显示可用命令列表
- `/clear` 清空会话并提示"会话已清空。"
- `/exit` 打印"再见！"并退出

**当前状态：** 应可通过

---

### L0-2：Mock 对话（不调工具）

**输入：**
```
我想学习 Python
```

**预期：**
- Agent Loop 使用 MockLLMClient 完成一轮对话
- 返回 mock 固定响应
- 不会崩溃或报错

**当前状态：** 应可通过（返回 "This is a mock response from MockLLMClient."）

---

### L0-3：Mock 对话（调工具模式）

**前置：** 需要先在 CLI 中注册至少一个 mock 工具（如 EchoTool），或修改 MockLLMClient 为 tool 模式

**输入：**
```
搜索 LangGraph 教程
```

**预期：**
- MockLLMClient 返回 tool_use 请求
- Agent Loop 查找工具、执行、回填结果
- 再调一次 LLM 获取最终回复

**当前状态：** 不可直接通过 —— `build_engine()` 创建空 ToolRegistry，且 MockLLMClient 未设为 tool 模式

---

### L0-4：Router 规则匹配

**前置：** Router 模块已有但未接入 CLI

**单独测试方法：**
```python
from app.core.router import InputRouter
r = InputRouter()
print(r.route("我想学习 LangGraph"))
print(r.route("https://github.com/huggingface/smolagents"))
print(r.route("复盘一下今天学的内容"))
```

**预期：**
- "我想学习 LangGraph" → `intent: learn_concept`
- GitHub URL → `intent: analyze_repo`
- "复盘" → `intent: review`

**当前状态：** 单元测试已覆盖（9 个用例全部通过），但未接入 CLI 流

---

### L0-5：Memory 存储读写

**前置：** MemoryStore 已有但未接入 CLI

**单独测试方法：**
```python
from app.memory.memory_store import MemoryStore
m = MemoryStore(base_dir="storage/memory/test")
m.save("test_topic", "project", "测试记忆", "- 学习 LangGraph\n")
found = m.find("test_topic")
print(found)
```

**预期：** 写入后能读出，Markdown 文件包含正确 frontmatter

**当前状态：** 单元测试已覆盖（4 个用例全部通过）

---

### L0-6：Session 持久化

**前置：** SessionStore 已有但未接入 CLI

**单独测试方法：**
```python
from app.memory.session_store import SessionStore
s = SessionStore(base_dir="storage/sessions/test")
s.append_message("s1", {"role": "user", "content": "hello"})
s.append_message("s1", {"role": "assistant", "content": "hi"})
msgs = s.get_messages("s1")
print(msgs)
```

**预期：** JSONL 文件正确写入和读取

**当前状态：** 单元测试已覆盖（3 个用例全部通过）

---

## L1 测试：真实 LLM 接入

这些测试需要配置 `.env` 中的 `DEEPSEEK_API_KEY`。

### L1-1：LLM 冒烟测试

**命令：**
```bash
python scripts/smoke_llm_real.py
```

**预期：**
- 小模型和大模型各发送一条请求
- 返回非空内容
- 无网络异常或认证错误

**当前状态：** 脚本已就绪，需要 `.env` 中填写 API key

---

### L1-2：真实 LLM + Mock Tools 闭环

**前置：** 需要在 CLI 中注册 mock 工具 + 使用 DeepSeekLLMClient

**描述：** 用真实 LLM 驱动 Agent Loop，但工具仍然 mock

**预期：**
- LLM 根据用户输入决定调用哪个工具
- Agent Loop 执行 mock 工具
- LLM 基于工具结果生成最终回复

**当前状态：** 需要少量代码改动即可实现（在 `build_engine` 中注册 mock 工具 + 使用 DeepSeekLLMClient + MockLLMClient 改为真实 client）

---

### L1-3：真实 LLM 学习概念解释

**输入：**
```
解释 LangGraph 的核心概念
```

**预期：**
- DeepSeek V4 Flash 返回有条理的概念解释
- 包含 StateGraph、Node、Edge、State、Checkpoint 等术语
- 回复使用中文

**当前状态：** 需要 L1-2 先通过

---

### L1-4：真实 LLM 学习路线生成

**输入：**
```
帮我规划一个 2 周学习 Rust 的路线
```

**预期：**
- 分阶段的学习计划
- 包含核心概念、实践项目、推荐资源

---

### L1-5：Tool Calling 稳定性测试

**描述：** 注册 3 个 mock 工具（search_web / read_url / save_note），让 LLM 决定调用哪个

**测试输入：**
```
1. "搜索 Python asyncio 教程"    → 应调用 search_web
2. "阅读 https://example.com"     → 应调用 read_url  
3. "保存这个学习笔记"             → 应调用 save_note
4. "今天天气怎么样"               → 不应调用任何工具
```

**预期：** LLM 在 4/4 场景下正确选择工具

---

### L1-6：JSON Action Fallback 测试

**描述：** 如果标准 tool calling 不稳定，验证 JSON action fallback

**LLM 输出格式：**
```json
{"action": "search_web", "arguments": {"query": "LangGraph tutorial"}}
```

**预期：** Agent Loop 能正确解析 JSON action 并执行对应工具

---

## L2 测试：搜索与网页读取

### L2-1：真实网页搜索

**描述：** 实现 RealSearchWeb 工具（如 Tavily / SerpAPI / DuckDuckGo）

**测试输入：**
```
搜索 LangGraph 官方文档
搜索 Python asyncio 最佳实践
搜索 Rust 所有权机制教程
```

**预期：** 返回带 URL 的搜索结果

---

### L2-2：真实网页读取

**描述：** 实现 RealReadUrl 工具（httpx + 正文提取）

**测试输入：**
```
阅读 https://docs.python.org/3/library/asyncio.html
总结这篇教程的主要内容
```

**预期：** 提取网页正文，LLM 生成总结

---

### L2-3：Router + 搜索 + 总结闭环

**描述：** 全链路测试：

```
用户："我想学习 WebAssembly"
→ Router 识别为 learn_concept
→ SearchWeb 搜索资料
→ ReadUrl 读取最佳结果
→ LLM 总结 + 生成学习路线
→ LearningTodoWrite 记录进度
```

---

## L3 测试：GitHub 仓库分析

### L3-1：公开 README 抓取

**描述：** 不需要 GitHub token，直接 HTTP 获取 raw README

**测试输入：**
```
https://github.com/huggingface/smolagents
https://github.com/langchain-ai/langgraph
```

**预期：** 正确获取 README 内容，提取项目描述、安装方式、快速开始

---

### L3-2：仓库目录结构分析

**描述：** 通过 GitHub REST API 或公开页面解析目录结构

**预期：** 识别核心模块、技术栈、关键文件

---

### L3-3：仓库学习路线生成

**描述：** 读取仓库后，生成从看懂到能改的学习路线

**预期：** 包含阅读顺序、关键文件说明、可模仿的项目建议

---

## 当前可立即验证的能力

```
┌──────────────────────────────────────────────────┐
│  ✅ L0-1：CLI 启动/退出                          │
│  ✅ L0-4：Router 规则匹配（单元测试）             │
│  ✅ L0-5：Memory 存储读写（单元测试）             │
│  ✅ L0-6：Session 持久化（单元测试）              │
│  ✅ L0-2：Mock 对话（返回固定 mock 回复）         │
│                                                  │
│  ⚠ L0-3：Mock 工具调用闭环（需注册工具）         │
│  ⚠ L1-1：LLM 冒烟测试（需配置 API key）          │
│  ⚠ L1-2：真实 LLM + Mock Tools（需少量连接代码） │
│                                                  │
│  ❌ L0（其他）：未接入主流程                       │
│  ❌ L1-3~6：需先完成 L1-2                         │
│  ❌ L2：SearchWeb/ReadUrl 一行未写                │
│  ❌ L3：ReadGitHubRepo 一行未写                   │
└──────────────────────────────────────────────────┘
```

---

## 建议验证顺序

1. **10 分钟**：确认 L0-1~L0-2（CLI mock 模式已可用）
2. **20 分钟**：完成 L0-3（注册 1 个 mock 工具到 CLI + 测试 tool calling 流程）
3. **15 分钟**：配置 `.env` + 跑 L1-1（LLM 冒烟测试）
4. **30 分钟**：完成 L1-2（连接真实 LLM + mock tools 的闭环）
5. **之后**：根据测试结果决定先实现 SearchWeb 还是先完善闭环
