<script setup lang="ts">
import { computed } from 'vue'
import { useSessionStore } from '../../stores/session'

const emit = defineEmits<{
  (e: 'select-session', id: string): void
  (e: 'create-session'): void
}>()

const sessionStore = useSessionStore()

const sortedSessions = computed(() => {
  return [...sessionStore.sessions].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  )
})

function formatTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function truncate(text: string, length: number): string {
  if (!text) return '新会话'
  return text.length > length ? text.substring(0, length) + '...' : text
}
</script>

<template>
  <aside class="w-64 bg-white/60 backdrop-blur-2xl border-r border-[#e8ecf1]/80 flex flex-col h-full">
    <!-- Logo -->
    <div class="p-5">
      <h1 class="text-lg font-semibold text-slate-800 flex items-center gap-2.5 tracking-tight">
        <span class="w-8 h-8 rounded-xl bg-gradient-to-br from-[#5b7fff] to-[#8b5cf6] flex items-center justify-center">
          <svg class="w-4.5 h-4.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
          </svg>
        </span>
        LearnAgent
      </h1>
    </div>

    <!-- 新建 -->
    <div class="px-3 pb-2">
      <button
        @click="emit('create-session')"
        class="w-full py-2.5 rounded-xl bg-gradient-to-r from-[#5b7fff] to-[#7c6ff7]
               hover:from-[#4b6fef] hover:to-[#6c5fe7]
               text-white text-sm font-medium transition-all duration-200
               shadow-[0_2px_8px_rgba(91,127,255,0.3)] hover:shadow-[0_4px_12px_rgba(91,127,255,0.4)]"
      >
        + 新会话
      </button>
    </div>

    <!-- 会话列表 -->
    <div class="flex-1 overflow-y-auto px-3 pb-3">
      <div class="space-y-0.5">
        <button
          v-for="session in sortedSessions"
          :key="session.id"
          @click="emit('select-session', session.id)"
          class="w-full px-3 py-2.5 rounded-xl text-left transition-all duration-150"
          :class="session.id === sessionStore.currentSessionId
            ? 'bg-white/90 shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-[#e8ecf1]/80'
            : 'hover:bg-white/50 border border-transparent'"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-slate-700 truncate">
                {{ session.topic || truncate(session.firstMessage, 16) || '新会话' }}
              </p>
              <p class="text-[0.7rem] text-slate-400 mt-0.5">
                {{ session.messageCount }} 条 · {{ formatTime(session.updatedAt) }}
              </p>
            </div>
            <span
              v-if="session.intent && session.intent !== 'chat'"
              class="px-2 py-0.5 text-[0.65rem] rounded-full bg-[#5b7fff]/10 text-[#5b7fff] font-medium"
            >{{ session.intent === 'learn_concept' ? '学习' : session.intent }}</span>
          </div>
        </button>
      </div>

      <div v-if="sortedSessions.length === 0" class="text-center py-12 text-slate-400">
        <svg class="w-10 h-10 mx-auto mb-3 opacity-40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <p class="text-sm">暂无会话</p>
      </div>
    </div>
  </aside>
</template>
