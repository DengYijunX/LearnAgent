# URL 记忆保存与网页读取兜底修复记录

## 背景

本次修复针对两个已知问题：

1. 当 URL 或包含 URL 的 topic 被用于长期记忆文件名时，`:`、`?` 等 Windows 文件名非法字符会导致保存失败，进而引发异常退出。
2. 部分网站对默认工具请求头有反爬限制。首次读取失败时，如果改用更接近普通浏览器的请求头，部分网页可以继续读取。

## 根因分析

### 记忆保存失败

当前 topic 会在 `app.core.query_engine.LearnQueryEngine.submit_message()` 中经过 `normalize_topic()`，并最终由 `MemoryStore.save()` 写入 Markdown 文件。

候选修复在 `app/core/router.py` 中增加了 topic 的非法字符过滤，这可以降低 URL topic 进入文件名的风险。但真正生成文件路径的是 `app/memory/memory_store.py` 的 `_path()` 方法，原逻辑只替换 `/` 和 `\`：

```python
safe = name.replace("/", "_").replace("\\", "_")
```

因此，只修 router 仍不能保证所有调用 `MemoryStore.save()` 的 name 都是安全文件名。

### 网页读取失败

`app/tools/read_url.py` 原逻辑只使用 LearnAgent 自身的 User-Agent 请求一次，并在 `response.raise_for_status()` 后直接返回错误。遇到 403 时没有第二条读取路径。

候选修复在 403 时增加一次浏览器式 User-Agent 请求，方向正确，且对现有成功路径影响较小。

## 最终修改方案

### 1. 存储层集中保证文件名安全

在 `app/memory/memory_store.py` 中扩展 `_path()`：

- 继续兼容原有 `/` 和 `\` 替换逻辑。
- 过滤 Windows 文件名非法字符：`< > : " | ? *` 以及控制字符。
- 合并连续下划线，清理首尾空白、点号和下划线。
- 当名称被额外改写或过长时追加原始 name 的 SHA1 短摘要，降低不同 name 被清理成同一文件名的碰撞风险。
- YAML frontmatter 中仍保留原始 `name`，不改变记忆内容语义。

### 2. topic 归一化增加防线

在 `app/core/router.py` 的 `normalize_topic()` 中过滤文件系统非法字符，并合并连续连字符。这样 UI、topic 管理和记忆描述也会得到更干净的 topic。

### 3. read_url 增加 403 兜底请求

在 `app/tools/read_url.py` 中：

- 第一次仍使用 LearnAgent 标识请求。
- 如果返回 403，再使用普通浏览器 User-Agent、`Accept-Language` 和 `Referer` 重试一次。
- 第二次仍失败时保持原有错误返回方式，不吞掉真实错误。

## 与候选代码的取舍

- 采纳：`router.py` 中过滤非法字符的思路。
- 采纳：`read_url.py` 中 403 后使用浏览器请求头重试的思路。
- 调整：没有只把文件名修复放在 router，因为保存失败的根因位于 `MemoryStore._path()`；最终方案在存储层做统一保护，router 作为前置防线。
- 未纳入：候选 `read_url.py` 中 `_meta` 和 `Last-Modified` 记录不属于本次两个已知问题的必要修复，暂不扩大改动范围。

## 回归测试

新增/更新测试覆盖：

- `tests/test_memory.py::TestMemoryStore::test_url_like_name_is_saved_with_safe_filename`
  - 验证 URL-like name 可以保存和读取，生成文件名不含 `:`、`?`。
- `tests/test_topic_management.py::TestTopicNormalization::test_filesystem_unsafe_characters_are_normalized`
  - 验证 URL topic 会被归一化为文件名友好的 topic。
- `tests/test_real_tools.py::TestRealReadUrl::test_retries_with_browser_headers_after_forbidden`
  - 使用 fake `httpx.AsyncClient` 验证首次 403 后会进行第二次浏览器式请求。

已执行定向测试：

```powershell
.\.venv\Scripts\python -m pytest -q -p no:cacheprovider tests/test_memory.py tests/test_topic_management.py tests/test_real_tools.py::TestRealReadUrl::test_retries_with_browser_headers_after_forbidden
```

结果：`20 passed`。

已执行全量测试：

```powershell
.\.venv\Scripts\python -m pytest -q -p no:cacheprovider
```

结果：`138 passed, 6 skipped`。
