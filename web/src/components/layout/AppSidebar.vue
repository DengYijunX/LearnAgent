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
  <aside class="w-64 bg-slate-950 border-r border-slate-800 flex flex-col h-full">
    <!-- Logo 区域 -->
    <div class="p-4 border-b border-slate-800">
      <h1 class="text-lg font-semibold text-white flex items-center gap-2">
        <svg class="w-6 h-6 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
        LearnAgent
      </h1>
    </div>

    <!-- 新建会话按钮 -->
    <div class="p-3">
      <button
        @click="emit('create-session')"
        class="w-full py-2 px-4 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors flex items-center justify-center gap-2 font-medium"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12h14" />
        </svg>
        新会话
      </button>
    </div>

    <!-- 会话列表 -->
    <div class="flex-1 overflow-y-auto px-3 pb-3">
      <div class="space-y-1">
        <button
          v-for="session in sortedSessions"
          :key="session.id"
          @click="emit('select-session', session.id)"
          class="w-full p-3 rounded-lg text-left transition-colors group"
          :class="[
            session.id === sessionStore.currentSessionId
              ? 'bg-slate-800 border border-slate-700'
              : 'hover:bg-slate-900 border border-transparent'
          ]"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-white truncate">
                {{ session.topic || truncate(session.firstMessage, 20) || '新会话' }}
              </p>
              <p class="text-xs text-slate-400 mt-1">
                {{ session.messageCount }} 条消息 · {{ formatTime(session.updatedAt) }}
              </p>
            </div>
            <span
              v-if="session.topic"
              class="px-2 py-0.5 text-xs rounded-full bg-slate-700 text-slate-300"
            >
              {{ session.topic }}
            </span>
          </div>
        </button>
      </div>

      <!-- 空状态 -->
      <div
        v-if="sortedSessions.length === 0"
        class="text-center py-8 text-slate-500"
      >
        <svg class="w-12 h-12 mx-auto mb-3 opacity-50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <p class="text-sm">暂无会话记录</p>
        <p class="text-xs mt-1">点击上方按钮开始新会话</p>
      </div>
    </div>
  </aside>
</template>
