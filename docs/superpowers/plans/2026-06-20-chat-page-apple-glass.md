# LearnAgent Chat Page Apple Glass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the existing desktop chat page as a polished Apple-inspired glass interface while preserving the current REST and WebSocket behavior.

**Architecture:** Keep the existing Vue 3 and Pinia data flow intact and limit changes to the application shell and chat-facing components. Introduce shared visual tokens in the global stylesheet, use Lucide Vue for all interface icons, and connect empty-state prompts to the existing composer through a small exposed draft API.

**Tech Stack:** Vue 3, TypeScript, Pinia, Tailwind CSS 3, Lucide Vue, Vite

---

## File map

- Modify `web/src/App.vue`: desktop shell and ambient background.
- Modify `web/src/style.css`: tokens, glass utilities, Markdown/code styling, motion accessibility.
- Modify `web/src/components/layout/AppSidebar.vue`: glass session navigation and loading/empty states.
- Modify `web/src/components/layout/AppHeader.vue`: topic, mode, connection and processing status.
- Modify `web/src/components/chat/ChatPanel.vue`: light layout, draft-fill coordination and visible connection feedback.
- Modify `web/src/components/chat/MessageList.vue`: constrained reading column and interactive empty state.
- Modify `web/src/components/chat/MessageBubble.vue`: document-like assistant output and user glass bubble.
- Modify `web/src/components/chat/ToolCallCard.vue`: compact light execution timeline with Lucide icons.
- Modify `web/src/components/chat/ChatInput.vue`: floating auto-growing composer and exposed draft API.
- Modify `web/src/components/common/PermissionModal.vue`: accessible light glass confirmation dialog.

### Task 1: Establish the shared visual system

**Files:**
- Modify: `web/src/style.css`
- Modify: `web/src/App.vue`

- [ ] **Step 1: Capture the current type baseline**

Run: `cd web; npm run check`

Expected: PASS. If it fails before edits, record the existing error and do not attribute it to the redesign.

- [ ] **Step 2: Add global design tokens and glass primitives**

Add CSS custom properties for canvas, surface, border, primary, text and semantic colors. Add reusable `.glass-panel`, `.glass-control`, `.focus-ring`, and `.app-noise` styles with visible light-mode borders and restrained shadows. Keep SF Pro/PingFang system typography and add `prefers-reduced-motion` rules that disable non-essential transforms and animations.

- [ ] **Step 3: Rebuild the application canvas**

Change `App.vue` from a flat `#f5f7fb` flex row to a full-height ambient canvas with pale blue/cyan radial light, a subtle noise layer, and a desktop two-column shell. Preserve the existing sidebar emits and `ChatPanel` ref calls exactly.

- [ ] **Step 4: Verify the shell compiles**

Run: `cd web; npm run check`

Expected: PASS with no Vue or TypeScript errors.

- [ ] **Step 5: Commit the visual foundation**

```powershell
git add web/src/App.vue web/src/style.css
git commit -m "feat(frontend): establish Apple glass visual system"
```

### Task 2: Rebuild desktop navigation and status header

**Files:**
- Modify: `web/src/components/layout/AppSidebar.vue`
- Modify: `web/src/components/layout/AppHeader.vue`

- [ ] **Step 1: Define observable acceptance states**

Before editing, list the rendered states to preserve: zero sessions, loading sessions, selected session, unselected session, plan/default mode, connecting/connected/disconnected WebSocket, processing turn, and completed tool statistics.

- [ ] **Step 2: Implement the glass session sidebar**

Use Lucide icons for brand, create action, messages and learning intent. Keep session sorting and event names unchanged. Add a loading skeleton driven by `sessionStore.isLoading`, an honest empty state, consistent focus rings, and a selected-session surface that does not shift layout on hover.

- [ ] **Step 3: Implement the compact status header**

Keep the current `toggle-mode` emit. Render the topic, permission mode, processing turns, up to three completed tool counts, and connection state with icon plus text so color is not the only signal. Use a translucent surface and prevent statistics from crowding the topic by truncating responsibly.

- [ ] **Step 4: Verify navigation and header types**

Run: `cd web; npm run check`

Expected: PASS.

- [ ] **Step 5: Commit navigation and status work**

```powershell
git add web/src/components/layout/AppSidebar.vue web/src/components/layout/AppHeader.vue
git commit -m "feat(frontend): refine chat navigation and status"
```

### Task 3: Build the empty state and floating composer interaction

**Files:**
- Modify: `web/src/components/chat/ChatPanel.vue`
- Modify: `web/src/components/chat/MessageList.vue`
- Modify: `web/src/components/chat/ChatInput.vue`

- [ ] **Step 1: Add an explicit prompt-selection contract**

Extend `MessageList` with an emit named `select-prompt` carrying a string. Extend `ChatInput` with an exposed `setDraft(content: string)` method that sets `inputValue` and focuses the textarea on the next tick. Hold a `ChatInput` ref in `ChatPanel` and forward prompt selections to `setDraft` without sending a message.

- [ ] **Step 2: Add the useful empty state**

Replace the dark circular placeholder with a restrained LearnAgent mark, a short capability statement, and three buttons containing realistic learning prompts. Emit `select-prompt` when a suggestion is clicked. Keep the state conditional on no messages and no active processing.

- [ ] **Step 3: Implement the floating auto-growing composer**

Preserve Enter-to-send, Shift+Enter newline, stop and disabled behavior. Resize the textarea after input and draft insertion up to 160px, reset it after send, use Lucide `ArrowUp` and `Square` icons, add accessible labels, and show context-aware helper text. The composer must remain disabled when no session exists.

- [ ] **Step 4: Remove residual dark layout and improve connection feedback**

Make `ChatPanel` transparent/light. Replace the anonymous top blue connecting strip with a readable connecting status integrated into the page without covering content.

- [ ] **Step 5: Verify the interaction contract**

Run: `cd web; npm run check`

Expected: PASS, including the exposed `setDraft` method and `select-prompt` payload types.

- [ ] **Step 6: Commit empty-state and composer work**

```powershell
git add web/src/components/chat/ChatPanel.vue web/src/components/chat/MessageList.vue web/src/components/chat/ChatInput.vue
git commit -m "feat(frontend): add guided empty state and composer"
```

### Task 4: Refine messages and tool execution presentation

**Files:**
- Modify: `web/src/components/chat/MessageBubble.vue`
- Modify: `web/src/components/chat/ToolCallCard.vue`
- Modify: `web/src/style.css`

- [ ] **Step 1: Preserve message rendering behavior**

Keep assistant Markdown sanitized through the existing `renderMarkdown` function and keep user content rendered as text. Preserve delegated code-copy behavior and timestamp formatting.

- [ ] **Step 2: Implement document-like messages**

Constrain assistant output to a readable surface with strong Markdown typography and code contrast. Keep user messages right-aligned in a pale blue glass bubble. Ensure long inline content and code blocks scroll internally instead of widening the page.

- [ ] **Step 3: Replace tool emoji with a semantic icon map**

Map common tool-name fragments to Lucide icons such as `Search`, `Globe`, `FileText`, `Terminal`, `Github`, `FolderOpen` and `Wrench`. Use `LoaderCircle`, `CircleCheck` and `CircleX` for status. Unknown tools fall back to `Wrench`.

- [ ] **Step 4: Implement the compact execution timeline**

Use a light bordered row with status rail, title, description, elapsed time and chevron. Keep running tools non-expandable and completed/failed tools expandable. Render result summaries, result titles and JSON input in high-contrast light surfaces.

- [ ] **Step 5: Verify message and tool types**

Run: `cd web; npm run check`

Expected: PASS.

- [ ] **Step 6: Commit message presentation**

```powershell
git add web/src/components/chat/MessageBubble.vue web/src/components/chat/ToolCallCard.vue web/src/style.css
git commit -m "feat(frontend): refine messages and tool timeline"
```

### Task 5: Rebuild permission confirmation honestly

**Files:**
- Modify: `web/src/components/common/PermissionModal.vue`

- [ ] **Step 1: Preserve the permission contract**

Keep the `confirm` and `deny` emits, `chatStore.pendingPermission` source, localized tool names, reason, parameter preview and optional content preview.

- [ ] **Step 2: Remove the non-functional remember choice**

Delete `rememberChoice`, its watcher, the checkbox, and the console-only behavior because no backend or store behavior implements the promised 60-second exemption.

- [ ] **Step 3: Implement an accessible light dialog**

Replace emoji with Lucide icons, use `role="dialog"`, `aria-modal="true"`, a labelled heading, visible keyboard focus and a light glass surface. Keep deny secondary and allow primary; use warning color only for the permission context icon and explanatory copy.

- [ ] **Step 4: Verify the dialog compiles**

Run: `cd web; npm run check`

Expected: PASS.

- [ ] **Step 5: Commit permission UI**

```powershell
git add web/src/components/common/PermissionModal.vue
git commit -m "feat(frontend): redesign permission confirmation"
```

### Task 6: Build and browser verification

**Files:**
- Modify only files required to fix issues found during verification.

- [ ] **Step 1: Run static verification**

Run: `cd web; npm run check`

Expected: PASS.

- [ ] **Step 2: Run the production build**

Run: `cd web; npm run build`

Expected: PASS and Vite emits production assets in `web/dist`.

- [ ] **Step 3: Run relevant backend regression tests**

Run: `.\.venv\Scripts\python -m pytest -q -p no:cacheprovider tests/test_persistence.py tests/test_agent_loop.py`

Expected: PASS; the UI-only change must not alter session persistence or agent-loop behavior.

- [ ] **Step 4: Inspect the rendered page at desktop widths**

Start the existing application and inspect 1280px, 1440px and 1920px widths. Verify empty state, session selection, prompt-to-draft, user/assistant messages, Markdown/code, tool running/done/error states, mode switch, connection states, stop button and permission dialog. Confirm no horizontal page overflow and no dark-theme remnants.

- [ ] **Step 5: Inspect accessibility behavior**

Tab through all controls, verify visible focus, inspect accessible button/dialog names, confirm status is readable without color, and emulate reduced motion.

- [ ] **Step 6: Re-run checks after any fixes**

Run: `cd web; npm run check; npm run build`

Expected: both commands PASS.

- [ ] **Step 7: Commit verification fixes if any**

```powershell
git add web/src
git commit -m "fix(frontend): polish chat page verification issues"
```
