<script setup lang="ts">
import { computed } from 'vue'
import { GraduationCap, Layers3, MessageSquare, Plus, Sparkles } from 'lucide-vue-next'
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
  <aside class="flex h-full w-[268px] shrink-0 flex-col border-r border-white/70 bg-white/46 backdrop-blur-3xl">
    <div class="px-5 pb-5 pt-6">
      <div class="flex items-center gap-3">
        <span class="relative flex h-10 w-10 items-center justify-center rounded-[14px] bg-[linear-gradient(145deg,#4f8cff,#245fda)] text-white shadow-[0_8px_20px_rgba(47,107,232,0.24),inset_0_1px_0_rgba(255,255,255,0.35)]">
          <Layers3 :size="20" :stroke-width="2.2" />
          <span class="absolute inset-[3px] rounded-[11px] border border-white/20" aria-hidden="true" />
        </span>
        <div>
          <h1 class="text-[17px] font-semibold tracking-[-0.025em] text-[var(--ink)]">LearnAgent</h1>
          <p class="mt-0.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[var(--ink-muted)]">Learning workspace</p>
        </div>
      </div>
    </div>

    <div class="px-3 pb-3">
      <button
        @click="emit('create-session')"
        class="focus-ring flex w-full cursor-pointer items-center justify-center gap-2 rounded-[13px] bg-[linear-gradient(145deg,#4b86fb,#2e6be8)] px-4 py-2.5 text-sm font-semibold text-white shadow-[0_8px_22px_rgba(46,107,232,0.2),inset_0_1px_0_rgba(255,255,255,0.28)] transition-[background-color,box-shadow] duration-200 hover:shadow-[0_10px_26px_rgba(46,107,232,0.28)]"
      >
        <Plus :size="17" :stroke-width="2.2" />
        新建会话
      </button>
    </div>

    <div class="flex items-center justify-between px-5 pb-2 pt-2">
      <span class="text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--ink-muted)]">最近会话</span>
      <span v-if="sortedSessions.length" class="text-[11px] tabular-nums text-[var(--ink-muted)]">{{ sortedSessions.length }}</span>
    </div>

    <div class="flex-1 overflow-y-auto px-3 pb-4">
      <div v-if="sessionStore.isLoading" class="space-y-2 px-1 pt-1" aria-label="正在加载会话">
        <div v-for="index in 4" :key="index" class="h-[62px] animate-pulse rounded-[15px] border border-white/50 bg-white/35" />
      </div>

      <div v-else-if="sortedSessions.length" class="space-y-1">
        <button
          v-for="session in sortedSessions"
          :key="session.id"
          @click="emit('select-session', session.id)"
          class="focus-ring group w-full cursor-pointer rounded-[15px] border px-3 py-2.5 text-left transition-[background-color,border-color,box-shadow] duration-200"
          :class="session.id === sessionStore.currentSessionId
            ? 'border-white/90 bg-white/76 shadow-[0_6px_18px_rgba(68,88,117,0.08),inset_0_1px_0_rgba(255,255,255,0.9)]'
            : 'border-transparent hover:border-white/60 hover:bg-white/42'"
        >
          <div class="flex items-start gap-2.5">
            <span class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-[9px] border border-white/70 bg-white/55 text-[var(--ink-muted)] shadow-sm transition-colors group-hover:text-[var(--primary)]">
              <GraduationCap v-if="session.intent === 'learn_concept'" :size="14" />
              <MessageSquare v-else :size="14" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-[13px] font-semibold tracking-[-0.01em] text-[var(--ink)]">
                {{ session.topic || truncate(session.firstMessage, 16) || '新会话' }}
              </p>
              <p class="mt-1 text-[11px] text-[var(--ink-muted)]">
                {{ session.messageCount }} 条 · {{ formatTime(session.updatedAt) }}
              </p>
            </div>
          </div>
        </button>
      </div>

      <div v-else class="mx-2 mt-8 rounded-[18px] border border-dashed border-[var(--line-strong)] bg-white/28 px-4 py-6 text-center">
        <Sparkles :size="20" class="mx-auto mb-3 text-[var(--primary)]" />
        <p class="text-[13px] font-semibold text-[var(--ink)]">从一个问题开始</p>
        <p class="mt-1 text-[11px] leading-5 text-[var(--ink-muted)]">创建会话后，学习记录会出现在这里。</p>
      </div>
    </div>

    <div class="mx-4 mb-4 flex items-center gap-2 rounded-[13px] border border-white/60 bg-white/32 px-3 py-2.5 text-[11px] text-[var(--ink-secondary)]">
      <span class="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_0_3px_rgba(52,211,153,0.12)]" />
      <span>本地工作区</span>
      <span class="ml-auto font-medium text-[var(--ink-muted)]">Desktop</span>
    </div>
  </aside>
</template>
