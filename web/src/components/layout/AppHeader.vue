<script setup lang="ts">
import { computed } from 'vue'
import { useSessionStore } from '../../stores/session'
import { useChatStore } from '../../stores/chat'

const emit = defineEmits<{
  (e: 'toggle-mode'): void
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
  <header class="h-12 bg-white/40 backdrop-blur-2xl border-b border-[#e8ecf1]/70 px-5 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <h2 class="text-sm font-semibold text-slate-700 tracking-tight">
        {{ sessionStore.currentTopic || 'LearnAgent' }}
      </h2>
      <span
        v-if="sessionStore.currentTopic"
        class="px-2 py-0.5 text-[0.65rem] rounded-full font-medium"
        :class="sessionStore.permissionMode === 'plan'
          ? 'bg-amber-100 text-amber-700'
          : 'bg-emerald-100 text-emerald-700'"
      >{{ modeLabel }}</span>

      <div v-if="chatStore.isProcessing" class="flex items-center gap-1.5 text-xs text-slate-500 ml-2">
        <svg class="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span>思考中 ({{ chatStore.currentTurn }}/{{ chatStore.maxTurns }})</span>
      </div>
    </div>

    <div class="flex items-center gap-3">
      <div v-if="toolStats && toolStats.toolEntries.length > 0" class="flex items-center gap-2 text-[0.7rem] text-slate-500">
        <span>{{ toolStats.turns }} 轮</span>
        <span v-for="[name, count] in toolStats.toolEntries.slice(0, 3)" :key="name"
              class="px-2 py-0.5 rounded-lg bg-slate-100 text-slate-600">
          {{ name }} {{ count }}
        </span>
      </div>

      <button
        @click="emit('toggle-mode')"
        class="text-xs px-3 py-1.5 rounded-lg font-medium transition-colors"
        :class="sessionStore.permissionMode === 'plan'
          ? 'bg-amber-50 text-amber-700 hover:bg-amber-100'
          : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'"
      >
        {{ modeLabel }}模式
      </button>

      <div class="w-2 h-2 rounded-full"
        :class="chatStore.wsConnected ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.4)]' : 'bg-slate-300'" />
    </div>
  </header>
</template>
