<script setup lang="ts">
import { computed } from 'vue'
import { Check, ChevronDown, CircleDot, Compass, LoaderCircle, PanelRightClose, PanelRightOpen, Sparkles, Wifi, WifiOff, Wrench } from 'lucide-vue-next'
import { useSessionStore } from '../../stores/session'
import { useChatStore } from '../../stores/chat'

defineProps<{ contextOpen: boolean }>()

const emit = defineEmits<{
  (e: 'toggle-mode'): void
  (e: 'toggle-context'): void
}>()

const sessionStore = useSessionStore()
const chatStore = useChatStore()

const modeLabel = computed(() =>
  sessionStore.permissionMode === 'plan' ? '探索' : '完整'
)

const toolStats = computed(() => {
  if (!chatStore.toolStatistics) return null
  const { turns, tools } = chatStore.toolStatistics
  const toolEntries = Object.entries(tools)
  return { turns, toolEntries }
})
</script>

<template>
  <header class="relative z-20 flex h-[66px] shrink-0 items-center justify-between border-b border-white/65 bg-white/36 px-6 backdrop-blur-2xl">
    <div class="flex min-w-0 items-center gap-3">
      <div class="min-w-0">
        <p class="text-[10px] font-semibold uppercase tracking-[0.15em] text-[var(--ink-muted)]">当前会话</p>
        <h2 class="mt-0.5 max-w-[380px] truncate text-[15px] font-semibold tracking-[-0.02em] text-[var(--ink)]">
        {{ sessionStore.currentTopic || 'LearnAgent' }}
        </h2>
      </div>

      <div v-if="chatStore.isProcessing" class="ml-2 flex items-center gap-2 rounded-full border border-blue-100/80 bg-blue-50/75 px-3 py-1.5 text-[11px] font-medium text-blue-700">
        <LoaderCircle :size="13" class="animate-spin" />
        <span>思考中 · {{ chatStore.currentTurn }}/{{ chatStore.maxTurns }} 轮</span>
      </div>
    </div>

    <div class="flex shrink-0 items-center gap-2.5">
      <div v-if="toolStats && toolStats.toolEntries.length > 0" class="mr-1 hidden items-center gap-1.5 text-[11px] text-[var(--ink-muted)] xl:flex">
        <Wrench :size="13" />
        <span>{{ toolStats.turns }} 轮</span>
        <span v-for="[name, count] in toolStats.toolEntries.slice(0, 3)" :key="name" class="rounded-lg border border-white/65 bg-white/46 px-2 py-1 text-[var(--ink-secondary)]">
          {{ name }} · {{ count }}
        </span>
      </div>

      <button
        type="button"
        class="focus-ring glass-control flex cursor-pointer items-center gap-2 rounded-[11px] px-3 py-2 text-[12px] font-semibold text-[var(--ink-secondary)] transition-colors duration-200 hover:bg-white/90"
        aria-controls="learning-context-panel"
        :aria-expanded="contextOpen"
        :aria-label="contextOpen ? '关闭学习上下文' : '打开学习上下文'"
        @click="emit('toggle-context')"
      >
        <PanelRightClose v-if="contextOpen" :size="14" />
        <PanelRightOpen v-else :size="14" />
        上下文
      </button>

      <button
        @click="emit('toggle-mode')"
        class="focus-ring glass-control flex cursor-pointer items-center gap-2 rounded-[11px] px-3 py-2 text-[12px] font-semibold text-[var(--ink-secondary)] transition-colors duration-200 hover:bg-white/90"
        :aria-label="`切换模式，当前为${modeLabel}模式`"
        :class="sessionStore.permissionMode === 'plan'
          ? 'text-amber-700'
          : 'text-blue-700'"
      >
        <Compass v-if="sessionStore.permissionMode === 'plan'" :size="14" />
        <Sparkles v-else :size="14" />
        {{ modeLabel }}模式
        <ChevronDown :size="13" class="opacity-55" />
      </button>

      <div
        class="glass-control flex items-center gap-2 rounded-[11px] px-3 py-2 text-[11px] font-semibold"
        :class="chatStore.wsConnected ? 'text-emerald-700' : 'text-[var(--ink-muted)]'"
        role="status"
      >
        <Wifi v-if="chatStore.wsConnected" :size="14" />
        <WifiOff v-else :size="14" />
        <span>{{ chatStore.wsConnected ? '已连接' : '未连接' }}</span>
        <Check v-if="chatStore.wsConnected" :size="12" />
        <CircleDot v-else :size="12" />
      </div>
    </div>
  </header>
</template>
