<script setup lang="ts">
import { computed, ref } from 'vue'
import { Eraser, PanelRightClose, Pin, PinOff, RefreshCw } from 'lucide-vue-next'
import CurrentTopicCard from './CurrentTopicCard.vue'
import LearningPlanCard from './LearningPlanCard.vue'
import RuntimeStatusCard from './RuntimeStatusCard.vue'
import MemorySummaryCard from './MemorySummaryCard.vue'
import SystemStatusCard from './SystemStatusCard.vue'
import ConfirmDialog from '../common/ConfirmDialog.vue'
import ToastViewport, { type ToastMessage } from '../common/ToastViewport.vue'
import { useChatStore } from '../../stores/chat'
import { useContextStore } from '../../stores/context'
import { useSessionStore } from '../../stores/session'
import type { RuntimeProcess } from '../../types/api'

defineProps<{ open: boolean; pinned: boolean; overlay: boolean }>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'toggle-pin'): void
  (e: 'refresh'): void
  (e: 'toggle-mode'): void
  (e: 'set-topic', topic: string): void
}>()

const chatStore = useChatStore()
const contextStore = useContextStore()
const sessionStore = useSessionStore()
const toolCalls = computed(() => Array.from(chatStore.activeToolCalls.values()))
const pendingAction = ref<'clear' | 'stop' | null>(null)
const selectedProcess = ref<RuntimeProcess | null>(null)
const toasts = ref<ToastMessage[]>([])
let toastId = 0

function notify(text: string, tone: ToastMessage['tone'] = 'success') {
  const id = ++toastId
  toasts.value.push({ id, text, tone })
  window.setTimeout(() => dismissToast(id), 3200)
}

function dismissToast(id: number) {
  toasts.value = toasts.value.filter(message => message.id !== id)
}

function requestStop(process: RuntimeProcess) {
  selectedProcess.value = process
  pendingAction.value = 'stop'
}

async function confirmAction() {
  if (pendingAction.value === 'clear') {
    chatStore.clearMessages()
    notify('当前会话视图已清空。')
  } else if (pendingAction.value === 'stop' && selectedProcess.value && sessionStore.currentSessionId) {
    const pid = selectedProcess.value.pid
    try {
      const stopped = await contextStore.stopProcess(pid, sessionStore.currentSessionId)
      notify(stopped ? `进程 ${pid} 已停止。` : `进程 ${pid} 未能停止。`, stopped ? 'success' : 'error')
    } catch {
      notify(`停止进程 ${pid} 失败。`, 'error')
    }
  }
  pendingAction.value = null
  selectedProcess.value = null
}
</script>

<template>
  <Transition name="context-panel">
    <aside
      v-if="open"
      id="learning-context-panel"
      class="z-40 flex h-full w-[308px] shrink-0 flex-col border-l border-white/75 bg-[#f5f8fc]/76 shadow-[-18px_0_48px_rgba(54,76,110,0.08)] backdrop-blur-2xl"
      :class="overlay ? 'absolute inset-y-0 right-0' : 'relative'"
      aria-label="学习上下文"
    >
      <header class="flex h-[66px] shrink-0 items-center justify-between border-b border-white/75 px-4">
        <div>
          <p class="text-[10px] font-semibold uppercase tracking-[0.13em] text-[var(--ink-muted)]">Learning context</p>
          <h2 class="mt-0.5 text-[14px] font-semibold text-[var(--ink)]">学习上下文</h2>
        </div>
        <div class="flex items-center gap-1">
          <button type="button" class="context-icon-button" :class="contextStore.isLoading ? 'animate-spin' : ''" aria-label="刷新上下文" @click="emit('refresh')"><RefreshCw :size="14" /></button>
          <button type="button" class="context-icon-button" :aria-label="pinned ? '取消固定面板' : '固定面板'" @click="emit('toggle-pin')"><PinOff v-if="pinned" :size="14" /><Pin v-else :size="14" /></button>
          <button type="button" class="context-icon-button" aria-label="关闭学习上下文" @click="emit('close')"><PanelRightClose :size="15" /></button>
        </div>
      </header>

      <div class="min-h-0 flex-1 space-y-3 overflow-y-auto p-3.5">
        <CurrentTopicCard :topic="sessionStore.currentTopic" :intent="sessionStore.currentSession?.intent || 'chat'" :mode="sessionStore.permissionMode" @set-topic="emit('set-topic', $event)" @toggle-mode="emit('toggle-mode')" />
        <LearningPlanCard :todos="contextStore.todos" :error="contextStore.errors.todos" />
        <RuntimeStatusCard :processes="contextStore.processes" :tool-calls="toolCalls" :tool-count="contextStore.tools.length" :error="contextStore.errors.processes || contextStore.errors.tools" @stop-process="requestStop" />
        <MemorySummaryCard :memories="contextStore.memories" :error="contextStore.errors.memories" />
        <SystemStatusCard :config="contextStore.config" :connected="chatStore.wsConnected" :error="contextStore.errors.config" />

        <section class="context-card" aria-labelledby="actions-card-title">
          <h3 id="actions-card-title" class="context-card-title">快捷操作</h3>
          <button type="button" class="focus-ring mt-2.5 flex w-full cursor-pointer items-center gap-2 rounded-[10px] px-2.5 py-2 text-left text-[11px] font-semibold text-[var(--ink-secondary)] transition hover:bg-white/85" @click="pendingAction = 'clear'">
            <Eraser :size="14" class="text-slate-500" /> 清空当前会话视图
          </button>
        </section>
      </div>
    </aside>
  </Transition>

  <ConfirmDialog
    :open="pendingAction !== null"
    :title="pendingAction === 'stop' ? '停止后台进程？' : '清空当前会话视图？'"
    :description="pendingAction === 'stop' ? `将停止 PID ${selectedProcess?.pid || ''}，正在执行的相关任务可能中断。` : '这只会清空浏览器中的消息视图，不会删除服务器上的会话记录。'"
    :confirm-label="pendingAction === 'stop' ? '停止进程' : '清空视图'"
    :danger="pendingAction === 'stop'"
    @confirm="confirmAction"
    @cancel="pendingAction = null; selectedProcess = null"
  />
  <ToastViewport :messages="toasts" @dismiss="dismissToast" />
</template>

<style scoped>
.context-panel-enter-active,
.context-panel-leave-active { transition: opacity 180ms ease, transform 220ms cubic-bezier(.2,.8,.2,1); }
.context-panel-enter-from,
.context-panel-leave-to { opacity: 0; transform: translateX(18px); }
</style>
