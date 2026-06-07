# testrecord4 问题同步记录

记录日期：2026-06-07

来源文件：`docs/testrecord4.md`

本文件用于同步测试侧在 `testrecord4.md` 中反馈的问题，区分当前已解决、部分解决和待解决项，并记录已采用或建议采用的处理方法。

## 总览

| 编号 | 测试记录 | 问题摘要 | 当前状态 |
|---|---|---|---|
| TR4-01 | 2026/6/4 question3 | 权限确认提示中命令/内容显示不完整，用户无法确认风险 | 已解决 |
| TR4-02 | 2026/6/4 question2 | workspace 路径不清晰，且创建文件出现 Permission denied | 已解决基础问题，旧环境 Permission denied 需实机复测 |
| TR4-03 | 2026/6/4 question1 | 用户要求“阅读此内容及其相关网站”，系统只读单页即总结 | 已解决基础能力 |
| TR4-04 | 2026/6/4 question1 | 搜索结果混入危险/低质量内容，存在安全和可信度问题 | 已解决基础过滤 |
| TR4-05 | 2026/6/3 question2 | 新问题与前文无关时，回答串到旧主题 OpenClaw | 部分解决，需真实 LLM 场景复测 |
| TR4-06 | 2026/6/3 question1 | 搜索/读取大量失败时，没有可靠资料仍继续输出或停在半截 | 已解决 |
| TR4-07 | 关联历史问题 | URL 作为 topic/文件名导致路径异常 | 已解决 |
| TR4-08 | 关联历史问题 | 部分网站 403 反爬时没有普通浏览器请求兜底 | 已解决 |

## 已解决项

### TR4-01 权限确认提示显示不完整

问题表现：

- 测试记录中执行 `python self_attention_demo.py` 时，确认提示和后续错误输出被截断。
- 长命令、长文件内容、长 todo 列表都会影响用户判断操作风险。

处理方法：

- 在 `app/main.py` 中新增 `_format_permission_value()`。
- `command` 字段完整展示，不截断可执行命令。
- `content` 字段展示字符数、前片段和尾片段，避免整段代码刷屏。
- `todos` 字段展示前几条和总数。
- `agent_loop._summarize_result()` 改为使用 `_compact_error_summary()`，长错误保留关键尾部路径，例如 `self_attention_demo.py`。

验证：

- `tests/test_cli_helpers.py::test_format_permission_value_preserves_full_command`
- `tests/test_cli_helpers.py::test_format_permission_value_summarizes_long_content`
- `tests/test_agent_loop.py::TestToolResultSummary::test_error_summary_preserves_path_tail`

### TR4-02 workspace 路径不清晰与 Permission denied

问题表现：

- 测试记录中出现 `workspace: storage\workspace\transformer`，用户认为创建文件路径不清晰。
- 后续多次出现 `写入失败：[Errno 13] Permission denied: 'E:\\code\\p\\pro\\LearnAgent\\storage\\works...`。

处理方法：

- 在 `app/main.py` 中新增 `_sync_workspace_tools_for_route()`。
- 主循环在调用 `engine.submit_message()` 前，先根据本轮 topic 和 intent 注册对应 workspace 工具，避免新主题第一轮工具调用仍绑定旧 `_default` workspace。
- `FileWrite` 对 `storage/workspace/...` 这类错误相对路径给出明确提示：只传 workspace 内相对路径，例如 `self_attention_demo.py`。

验证：

- `tests/test_cli_helpers.py::test_sync_workspace_tools_for_route_registers_topic_workspace`
- `tests/test_cli_helpers.py::test_sync_workspace_tools_for_route_ignores_chat_without_topic`
- `tests/test_workspace_tools.py::TestFileWrite::test_rejects_storage_workspace_prefixed_path_with_guidance`

剩余注意：

- 旧日志里的 `Permission denied` 来自历史运行环境，当前修复覆盖了最可能的注册时机和错误路径问题；仍建议在真实 CLI 上复测一次 transformer 动手练习。

### TR4-03 指定“相关网站”时只读单页

问题表现：

- 用户输入“阅读此内容及其相关网站”，系统只读取用户提供的单个 URL，然后直接总结。

处理方法：

- 在 `app/context/context_builder.py` 中增加系统约束：用户要求“相关网站/相关链接/站内相关内容”时，必须继续搜索或抽取相关页面；如果只读取当前页面，不能声称完整阅读相关网站。
- 在 `app/tools/read_url.py` 中新增同域链接提取，返回到 `metadata.links`，为后续相关页面读取提供可用候选链接。

验证：

- `tests/test_skills_integration.py::TestSkillInjection::test_prompt_requires_related_site_expansion`
- `tests/test_real_tools.py::TestRealReadUrl::test_extracts_same_domain_links_for_related_reading`

### TR4-04 搜索结果安全与可信度过滤不足

问题表现：

- 搜索结果混入暗网、成人、低质量、无关站点标题。

处理方法：

- 在 `app/tools/search_web.py` 中增加基础安全过滤。
- 过滤成人、博彩、暗网、黑料、明显垃圾标题和已知危险域名。
- 返回 `filtered_count`，便于观察过滤数量。

验证：

- `tests/test_real_tools.py::TestRealSearchWeb::test_filters_unsafe_search_results`

### TR4-06 无可靠资料时缺少兜底回答

问题表现：

- 搜索/读取大量失败后，系统可能停在“让我搜索一下”，或没有给出明确的资料不足说明。

处理方法：

- 在 `app/core/agent_loop.py` 中新增 `_build_max_turns_fallback()`。
- 当工具失败且轮次耗尽、没有足够成功内容时，自动追加用户可见回答：
  - 明确说明“资料不足，当前无法可靠确认结论”。
  - 列出最近几条失败信息。
  - 给出下一步建议。

验证：

- `tests/test_agent_loop.py::TestAgentLoop::test_adds_fallback_when_tools_fail_and_turns_exhausted`

### TR4-07 URL topic/记忆文件名路径异常

问题表现：

- URL 或包含 URL 的 topic 被用于工作区或记忆文件名时，可能带入 `:`、`?` 等 Windows 文件名非法字符。
- 旧实现中 `MemoryStore._path()` 只替换 `/` 和 `\`，对 Windows 其他非法字符保护不足。

处理方法：

- 在 `app/core/router.py` 的 `normalize_topic()` 中增加文件系统非法字符过滤，topic 会被归一化为更安全的短标识。
- 在 `app/memory/memory_store.py` 的 `_path()` 中集中做文件名安全化，过滤 `< > : " | ? *` 和控制字符。
- 当 name 被改写或过长时追加 SHA1 短摘要，减少清理后文件名碰撞。
- 原始 `name` 仍保存在 YAML frontmatter 中，不丢失语义。

验证：

- `tests/test_memory.py::TestMemoryStore::test_url_like_name_is_saved_with_safe_filename`
- `tests/test_topic_management.py::TestTopicNormalization::test_filesystem_unsafe_characters_are_normalized`

关联文档：

- `docs/url-memory-and-read-url-fix.md`

### TR4-08 read_url 403 反爬兜底

问题表现：

- 部分网站用 LearnAgent 默认 User-Agent 请求时会返回 403。
- 旧实现首次请求失败后直接返回错误。

处理方法：

- `app/tools/read_url.py` 中保留第一次 LearnAgent 身份请求。
- 如果响应码为 403，再使用普通浏览器 User-Agent、`Accept-Language` 和 `Referer` 进行第二次请求。
- 第二次仍失败时继续返回错误，不吞掉真实失败原因。

验证：

- `tests/test_real_tools.py::TestRealReadUrl::test_retries_with_browser_headers_after_forbidden`

## 部分解决项

### TR4-05 上下文串扰，旧主题回答覆盖新问题

问题表现：

- 用户从 OpenClaw 话题切到“华南师范大学的校招是什么时候”。
- 系统进行了搜索，但最终输出仍是 OpenClaw 的旧回答。

已处理：

- 在 `app/context/context_builder.py` 中增加系统约束：只回答用户最新输入的问题，不要复用旧主题、旧结论或上一轮回答覆盖新问题。
- 在 `app/core/agent_loop.py` 中增加资料不足兜底，避免工具失败后停在旧回答或空回答。

验证：

- `tests/test_skills_integration.py::TestSkillInjection::test_prompt_requires_answering_latest_user_request`
- `tests/test_agent_loop.py::TestAgentLoop::test_adds_fallback_when_tools_fail_and_turns_exhausted`

剩余注意：

- 这是 LLM 行为类问题，当前通过系统约束和失败兜底降低复发概率。
- 仍建议后续增加真实或半模拟端到端测试：OpenClaw 问答后切到“华南师范大学校招时间”，最终回答不得包含 OpenClaw 摘要。

## 待解决项

暂无完全未处理项。仍需后续真实场景复测的是 TR4-02 和 TR4-05。

## 建议优先级

1. 继续复测：TR4-05 上下文串扰真实 LLM 场景。
2. 继续复测：TR4-02 transformer 动手练习首轮写文件。
3. 后续增强：TR4-04 搜索安全过滤可以继续扩展可信源排序和域名策略。
4. 后续增强：TR4-03 可进一步新增专门的相关链接读取工具。

## 后续处理建议

本轮已按三批完成基础修复：

1. 可靠回答批：TR4-05 + TR4-06
   - 已增加最新问题约束和资料不足兜底。

2. 搜索安全批：TR4-04 + TR4-03
   - 已增加搜索基础安全过滤和 `read_url` 同域链接 metadata。

3. 执行体验批：TR4-01 + TR4-02
   - 已增强权限显示、错误摘要、workspace 提前注册和错误路径提示。

## 当前验证基线

最近一次合并到 `main` 后已执行：

```powershell
python -m pytest -q -p no:cacheprovider
```

结果：`138 passed, 6 skipped`。

本轮新增定向回归测试已执行：

```powershell
.\.venv\Scripts\python -m pytest -q -p no:cacheprovider tests/test_real_tools.py::TestRealSearchWeb::test_filters_unsafe_search_results tests/test_real_tools.py::TestRealReadUrl::test_extracts_same_domain_links_for_related_reading tests/test_workspace_tools.py::TestFileWrite::test_rejects_storage_workspace_prefixed_path_with_guidance tests/test_agent_loop.py::TestAgentLoop::test_adds_fallback_when_tools_fail_and_turns_exhausted tests/test_agent_loop.py::TestToolResultSummary::test_error_summary_preserves_path_tail tests/test_skills_integration.py::TestSkillInjection::test_prompt_requires_answering_latest_user_request tests/test_skills_integration.py::TestSkillInjection::test_prompt_requires_related_site_expansion tests/test_cli_helpers.py
```

结果：`11 passed`。
