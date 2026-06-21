# LearnAgent Web Learning Context Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an adaptive desktop learning-context panel that exposes real CLI-era topic, Todo, tool, process, memory, and system state in the Web chat experience.

**Architecture:** Extend the existing in-memory Web session model and FastAPI routes with Todo and memory reads, then synchronize Todo/topic/cancel changes through explicit WebSocket events. On the frontend, introduce a dedicated Pinia context store and a 300px adaptive panel composed of focused cards; keep WebSocket ownership in `useWebSocket` and keep panel preference local to the browser.

**Tech Stack:** FastAPI, asyncio, pytest, Vue 3, TypeScript, Pinia, Tailwind CSS, Lucide Vue, Vite

---

## File map

- Modify `app/server/session_manager.py`: session-scoped Todo state and update API.
- Modify `app/server/routes.py`: memories and session Todo REST endpoints.
- Modify `app/server/app.py`: Todo event propagation, cancel handling, and topic updates.
- Modify `app/tools/todo_tools.py`: notify the Web session after Todo writes.
- Create `tests/test_web_context.py`: server context and protocol regression coverage.
- Modify `web/src/types/api.ts`: Todo, memory, process and config wire types.
- Modify `web/src/types/ws.ts`: `todo_update`, `cancelled`, and `set_topic` events.
- Modify `web/src/api/client.ts`: context API methods.
- Create `web/src/stores/context.ts`: panel data, loading, error, refresh and stale-request control.
- Modify `web/src/composables/useWebSocket.ts`: consume context events and send topic updates.
- Create `web/src/composables/useContextPanel.ts`: responsive default and local preference.
- Create `web/src/components/common/ToastViewport.vue`: lightweight status feedback.
- Create `web/src/components/common/ConfirmDialog.vue`: reusable keyboard-accessible confirmation.
- Create `web/src/components/context/LearningContextPanel.vue`: panel shell and composition.
- Create `web/src/components/context/CurrentTopicCard.vue`: topic and mode controls.
- Create `web/src/components/context/LearningPlanCard.vue`: Todo summary and statuses.
- Create `web/src/components/context/RuntimeStatusCard.vue`: tools and background processes.
- Create `web/src/components/context/MemorySummaryCard.vue`: recent learning memories.
- Create `web/src/components/context/SystemStatusCard.vue`: safe configuration and connection summary.
- Modify `web/src/components/chat/ChatPanel.vue`: mount panel, wire actions and context loading.
- Modify `web/src/components/layout/AppHeader.vue`: accessible panel toggle.
- Modify `web/src/App.vue`: allow adaptive third column without changing the left sidebar.
- Modify `web/src/style.css`: panel/drawer transition and desktop layout support.

### Task 1: Add session Todo state and context REST APIs

**Files:**
- Modify: `app/server/session_manager.py`
- Modify: `app/server/routes.py`
- Modify: `app/server/app.py`
- Test: `tests/test_web_context.py`

- [ ] **Step 1: Write failing SessionManager Todo tests**

Create `tests/test_web_context.py` with:

```python
import pytest

from app.server.session_manager import SessionManager


@pytest.mark.asyncio
async def test_session_manager_replaces_todo_snapshot():
    manager = SessionManager()
    session = await manager.create_session(topic="FastAPI")
    todos = [{"content": "阅读路由", "active_form": "正在阅读路由", "status": "in_progress"}]

    updated = await manager.update_todos(session.session_id, todos)

    assert updated is not None
    assert updated.todos == todos
    assert (await manager.get_session(session.session_id)).todos == todos


@pytest.mark.asyncio
async def test_session_manager_copies_todo_input():
    manager = SessionManager()
    session = await manager.create_session()
    todos = [{"content": "练习", "status": "pending"}]
    await manager.update_todos(session.session_id, todos)
    todos[0]["status"] = "completed"
    assert session.todos[0]["status"] == "pending"
```

- [ ] **Step 2: Run the Todo tests and verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_web_context.py`

Expected: FAIL because `Session.todos` and `SessionManager.update_todos` do not exist.

- [ ] **Step 3: Implement session-scoped Todo snapshots**

Add `todos: List[Dict[str, Any]] = field(default_factory=list)` to `Session`. Add `update_todos(session_id, todos)` that takes the manager lock, copies every dict, updates `updated_at`, and returns the session or `None`.

- [ ] **Step 4: Add route helper tests**

Extend `tests/test_web_context.py`:

```python
from app.server.routes import _bounded_memory, _format_todo


def test_bounded_memory_does_not_expose_unbounded_body():
    item = {"name": "topic_x", "description": "学习记录", "type": "learning", "body": "x" * 1000}
    result = _bounded_memory(item, body_limit=120)
    assert result["body"] == "x" * 120
    assert set(result) == {"name", "description", "type", "body"}


def test_format_todo_normalizes_active_form():
    result = _format_todo({"content": "读文档", "activeForm": "正在读文档", "status": "pending"})
    assert result == {"content": "读文档", "active_form": "正在读文档", "status": "pending"}
```

- [ ] **Step 5: Run helper tests and verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_web_context.py`

Expected: FAIL because `_bounded_memory` and `_format_todo` do not exist.

- [ ] **Step 6: Implement safe context routes**

Add `get_memory_store()` to `app/server/app.py`. In `routes.py`, add:

- `_format_todo()` accepting `active_form` or `activeForm` and restricting status to the three supported values.
- `_bounded_memory()` returning only `name`, `description`, `type`, and truncated `body`.
- `GET /api/sessions/{session_id}/todos`, returning 404 for unknown sessions.
- `GET /api/memories`, clamping `limit` to 1–50 and filtering by requested type.

- [ ] **Step 7: Run server context tests and full relevant tests**

Run: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_web_context.py tests/test_memory.py tests/test_persistence.py`

Expected: PASS.

- [ ] **Step 8: Commit server context APIs**

```powershell
git add app/server/session_manager.py app/server/routes.py app/server/app.py tests/test_web_context.py
git commit -m "功能（服务端）：提供学习上下文数据接口"
```

### Task 2: Complete Todo, cancel, and topic WebSocket behavior

**Files:**
- Modify: `app/server/app.py`
- Modify: `app/tools/todo_tools.py`
- Modify: `app/core/session_context.py`
- Test: `tests/test_web_context.py`

- [ ] **Step 1: Write failing normalization and cancellation tests**

Add pure helpers to the intended API in tests first:

```python
import asyncio
from app.server.app import _normalise_todos, _cancel_task


def test_normalise_todos_rejects_invalid_status():
    todos = _normalise_todos([{"content": "A", "status": "unknown"}])
    assert todos == [{"content": "A", "active_form": None, "status": "pending"}]


@pytest.mark.asyncio
async def test_cancel_task_waits_for_cancellation():
    started = asyncio.Event()

    async def worker():
        started.set()
        await asyncio.sleep(30)

    task = asyncio.create_task(worker())
    await started.wait()
    assert await _cancel_task(task) is True
    assert task.cancelled()
```

- [ ] **Step 2: Run tests and verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_web_context.py`

Expected: FAIL because the helpers do not exist.

- [ ] **Step 3: Implement explicit protocol behavior**

- Add `_normalise_todos()` and `_cancel_task()` in `app/server/app.py`.
- In the WebSocket loop, handle `cancel` by cancelling `agent_task`, sending `cancelled`, and leaving the connection open.
- Handle `set_topic` by trimming input, rejecting empty or path-like values, updating the session, and sending `topic_change`.
- Remove no-longer-used Web `command` assumptions; do not add CLI command parsing to the server socket.

- [ ] **Step 4: Publish Todo updates from the tool result**

Use `current_session_id` plus a session-scoped callback context so `LearningTodoWrite.call()` can persist the normalized snapshot and emit `todo_update` after a successful call. Preserve CLI behavior when no Web callback exists.

- [ ] **Step 5: Run Web protocol and agent tests**

Run: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_web_context.py tests/test_agent_loop.py tests/test_plan_mode.py`

Expected: PASS.

- [ ] **Step 6: Commit WebSocket behavior**

```powershell
git add app/server/app.py app/tools/todo_tools.py app/core/session_context.py tests/test_web_context.py
git commit -m "功能（服务端）：同步学习计划并支持取消任务"
```

### Task 3: Add frontend context types, API client, and store

**Files:**
- Modify: `web/src/types/api.ts`
- Modify: `web/src/types/ws.ts`
- Modify: `web/src/api/client.ts`
- Create: `web/src/stores/context.ts`
- Modify: `web/src/composables/useWebSocket.ts`

- [ ] **Step 1: Define typed context contracts**

Add `LearningTodo`, `LearningMemory`, `RuntimeProcess`, `ContextConfig`, `TodosResponse`, `MemoriesResponse`, and `ProcessesResponse`. Add `WsTodoUpdate` and `WsCancelled` to server events and `WsSetTopic` to client events. Remove `WsCommand` from the client union and `sendCommand` from `useWebSocket`.

- [ ] **Step 2: Implement API client methods**

Add `contextApi.getTodos(sessionId)`, `getMemories(limit)`, `getProcesses(sessionId)`, `stopProcess(pid, sessionId)`, `getConfig()`, all through the existing `request<T>()` helper.

- [ ] **Step 3: Implement the context store**

Create `useContextStore` with:

- `todos`, `memories`, `processes`, `config`, `isLoading`, `errors`, `lastRefreshedAt`.
- `load(sessionId)` using `Promise.allSettled` so one endpoint failure does not block other sections.
- A monotonically increasing request token so stale responses from a prior session are ignored.
- `refreshProcesses(sessionId)`, `stopProcess(pid, sessionId)`, `setTodos(snapshot)`, `clear()`.

- [ ] **Step 4: Wire WebSocket context events**

On `todo_update`, replace the Todo snapshot. On `cancelled`, stop the processing state without adding an error message. Add `sendSetTopic(topic)`.

- [ ] **Step 5: Verify frontend contracts compile**

Run: `npm --prefix web run check`

Expected: PASS.

- [ ] **Step 6: Commit context state layer**

```powershell
git add web/src/types web/src/api/client.ts web/src/stores/context.ts web/src/composables/useWebSocket.ts
git commit -m "功能（前端）：建立学习上下文状态层"
```

### Task 4: Build shared feedback and responsive panel shell

**Files:**
- Create: `web/src/composables/useContextPanel.ts`
- Create: `web/src/components/common/ToastViewport.vue`
- Create: `web/src/components/common/ConfirmDialog.vue`
- Create: `web/src/components/context/LearningContextPanel.vue`
- Modify: `web/src/App.vue`
- Modify: `web/src/components/chat/ChatPanel.vue`
- Modify: `web/src/components/layout/AppHeader.vue`
- Modify: `web/src/style.css`

- [ ] **Step 1: Implement panel preference rules**

`useContextPanel` must:

- Default open at `min-width: 1440px` when no saved preference exists.
- Default closed below 1440px.
- Store explicit user choice under `learnagent.context-panel.open`.
- Expose `isOpen`, `isPinned`, `toggle`, `close`, and `togglePinned`.
- Remove the media listener on unmount.

- [ ] **Step 2: Build reusable feedback components**

`ToastViewport` renders typed success/error messages with dismiss buttons and `aria-live="polite"`. `ConfirmDialog` uses `role="dialog"`, initial focus on the safe cancel action, Escape cancellation, Tab containment, and focus restoration via the parent trigger.

- [ ] **Step 3: Build the context panel shell**

Create a 300px glass panel with heading, last refresh label, refresh, pin, and close controls. Render slots or imported section cards inside a scrollable body. In unpinned narrow mode, render as an overlay drawer; in pinned wide mode, consume layout width.

- [ ] **Step 4: Wire layout and header toggle**

- Add `toggle-context`, `context-open`, and `aria-controls` support to `AppHeader`.
- Mount `LearningContextPanel` beside the central chat column in `ChatPanel`.
- Load/clear context on current session changes.
- Keep the left sidebar unchanged.

- [ ] **Step 5: Verify shell compilation**

Run: `npm --prefix web run check`

Expected: PASS.

- [ ] **Step 6: Commit panel foundation**

```powershell
git add web/src/composables/useContextPanel.ts web/src/components/common web/src/components/context/LearningContextPanel.vue web/src/App.vue web/src/components/chat/ChatPanel.vue web/src/components/layout/AppHeader.vue web/src/style.css
git commit -m "功能（前端）：加入自适应学习上下文面板"
```

### Task 5: Add real context cards and actions

**Files:**
- Create: `web/src/components/context/CurrentTopicCard.vue`
- Create: `web/src/components/context/LearningPlanCard.vue`
- Create: `web/src/components/context/RuntimeStatusCard.vue`
- Create: `web/src/components/context/MemorySummaryCard.vue`
- Create: `web/src/components/context/SystemStatusCard.vue`
- Modify: `web/src/components/context/LearningContextPanel.vue`
- Modify: `web/src/components/chat/ChatPanel.vue`

- [ ] **Step 1: Build current topic controls**

Render topic, intent and mode. An explicit edit button opens a compact input; submit through `sendSetTopic`, cancel without mutation, and reject blank values locally. Reuse the existing mode-toggle path.

- [ ] **Step 2: Build learning plan statuses**

Sort `in_progress`, `pending`, then `completed`. Show active and pending items by default, provide a completed-count disclosure, and render the exact empty message from the spec when no Todo exists.

- [ ] **Step 3: Build runtime status**

Read active tools from `chatStore`, available tool count from the API result, and processes from `contextStore`. Provide a confirmed stop action and refresh the list only after the API confirms success.

- [ ] **Step 4: Build memory and system cards**

Render at most three learning memories with accessible disclosure buttons. Show only model mode, API-key configured status, and WebSocket connection; never render `base_url`, `storage_dir`, or secret values.

- [ ] **Step 5: Add quick actions**

Add mode toggle, refresh context, and confirmed `chatStore.clearMessages()` actions. Explain that clear affects the current view and not long-term memory.

- [ ] **Step 6: Verify component compilation and build**

Run: `npm --prefix web run check; npm --prefix web run build`

Expected: PASS; Vite may retain its existing chunk-size warning but must emit assets.

- [ ] **Step 7: Commit real context cards**

```powershell
git add web/src/components/context web/src/components/chat/ChatPanel.vue
git commit -m "功能（前端）：展示主题计划进程与长期记忆"
```

### Task 6: Regression and browser verification

**Files:**
- Modify only files required by reproduced verification failures.

- [ ] **Step 1: Run fresh static and server verification**

Run:

```powershell
npm --prefix web run check
npm --prefix web run build
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Expected: frontend checks pass and Python reports no failures. If Windows resolves the wrong `python` inside `RunCode` tests, use a temporary test-only shim targeting `.venv` and remove it before completion.

- [ ] **Step 2: Run the app and verify 1280px**

At 1280×900 confirm the panel defaults closed, opens as a drawer, closes with Escape, returns focus, does not shift message scroll, and creates no horizontal overflow.

- [ ] **Step 3: Verify 1440px and preference persistence**

At 1440×900 confirm the panel defaults open with no saved preference. Toggle closed, reload, confirm it remains closed; clear the test preference and confirm responsive default returns.

- [ ] **Step 4: Verify real data states**

Exercise empty and populated Todo, memory, tool, process and config states. Switch sessions and confirm prior-session Todo/process data disappears before new data renders. Confirm one endpoint failure leaves other cards usable.

- [ ] **Step 5: Verify destructive and task controls**

Confirm stop Agent sends `cancel`, stop process requires confirmation and refreshes after success, clear view requires confirmation, and topic edit updates the current session.

- [ ] **Step 6: Inspect console and accessibility**

Confirm no relevant errors/warnings, all controls have accessible names, panel state updates `aria-expanded`, status is not color-only, and reduced-motion behavior removes non-essential transitions.

- [ ] **Step 7: Commit verification fixes when needed**

```powershell
git add app web tests
git commit -m "修复（前端）：完善学习上下文面板验证问题"
```
