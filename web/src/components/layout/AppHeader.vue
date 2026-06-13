<script setup lang="ts">
import { computed } from 'vue'
import { useSessionStore } from '../../stores/session'
import { useChatStore } from '../../stores/chat'
import StatusBadge from '../common/StatusBadge.vue'

const emit = defineEmits<{
  (e: 'toggle-mode'): void
}>()

const sessionStore = useSessionStore()
const chatStore = useChatStore()

const modeLabel = computed(() =>
  sessionStore.permissionMode === 'plan' ? '探索模式' : '完整模式'
)

const modeColor = computed(() =>
  sessionStore.permissionMode === 'plan' ? 'warning' : 'success'
)

const toolStats = computed(() => {
  if (!chatStore.toolStatistics) return null
  const { turns, tools } = chatStore.toolStatistics
  const toolEntries = Object.entries(tools)
  return { turns, toolEntries }
})
</script>

<template>
  <header class="h-14 border-b border-slate-700 bg-slate-900 px-4 flex items-center justify-between">
    <!-- 左侧：主题和意图 -->
    <div class="flex items-center gap-3">
      <!-- 主题名称 -->
      <h2 class="text-white font-medium">
        {{ sessionStore.currentTopic || '学习助手' }}
      </h2>

      <!-- 意图标签 -->
      <StatusBadge
        v-if="sessionStore.currentTopic"
        :status="sessionStore.permissionMode"
        :label="modeLabel"
      />

      <!-- 处理状态 -->
      <div
        v-if="chatStore.isProcessing"
        class="flex items-center gap-2 text-sm text-slate-400"
      >
        <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <span>思考中 ({{ chatStore.currentTurn }}/{{ chatStore.maxTurns }})</span>
      </div>
    </div>

    <!-- 右侧：模式和工具统计 -->
    <div class="flex items-center gap-4">
      <!-- 工具统计 -->
      <div
        v-if="toolStats && toolStats.toolEntries.length > 0"
        class="flex items-center gap-2 text-xs text-slate-400"
      >
        <span>{{ toolStats.turns }} 轮</span>
        <span class="text-slate-600">·</span>
        <span
          v-for="[name, count] in toolStats.toolEntries.slice(0, 3)"
          :key="name"
          class="px-2 py-0.5 bg-slate-800 rounded"
        >
          {{ name }}: {{ count }}
        </span>
      </div>

      <!-- 模式切换 -->
      <button
        @click="emit('toggle-mode')"
        class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors"
        :class="[
          sessionStore.permissionMode === 'plan'
            ? 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30'
            : 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30'
        ]"
      >
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path v-if="sessionStore.permissionMode === 'plan'" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          <path v-else d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {{ modeLabel }}
      </button>

      <!-- 连接状态 -->
      <div
        class="w-2 h-2 rounded-full"
        :class="chatStore.wsConnected ? 'bg-emerald-500' : 'bg-slate-600'"
        :title="chatStore.wsConnected ? '已连接' : '未连接'"
      />
    </div>
  </header>
</template>
