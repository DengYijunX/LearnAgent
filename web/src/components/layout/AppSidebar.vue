<script setup lang="ts">
import { ref, computed } from 'vue'
import { GraduationCap, Layers3, MessageSquare, MoreHorizontal, Pencil, Plus, Sparkles, Trash2 } from 'lucide-vue-next'
import { useSessionStore } from '../../stores/session'
import { sessionApi } from '../../api/client'

const emit = defineEmits<{
  (e: 'select-session', id: string): void
  (e: 'create-session'): void
}>()

const sessionStore = useSessionStore()

// 当前打开的菜单（会话 ID），null 表示关闭
const openMenuId = ref<string | null>(null)
const menuPosition = ref({ x: 0, y: 0 })
// 重命名状态
const renamingId = ref<string | null>(null)
const renameValue = ref('')

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

function toggleMenu(id: string, e: Event) {
  e.stopPropagation()
  if (openMenuId.value === id) {
    openMenuId.value = null
    return
  }
  const btn = e.currentTarget as HTMLElement
  const rect = btn.getBoundingClientRect()
  menuPosition.value = { x: rect.left - 100, y: rect.bottom + 4 }
  openMenuId.value = id
}

function closeMenu() {
  openMenuId.value = null
  renamingId.value = null
}

function startRename(e: Event) {
  e.stopPropagation()
  const id = openMenuId.value
  if (!id) return
  const session = sessionStore.sessions.find(s => s.id === id)
  renameValue.value = session?.topic || ''
  renamingId.value = id
  openMenuId.value = null
}

async function confirmRename() {
  const id = renamingId.value
  if (!id) return
  const topic = renameValue.value.trim()
  try {
    await sessionApi.renameSession(id, topic)
    sessionStore.updateSessionTopic(id, topic || null as any)
  } catch (e) {
    console.error('Failed to rename session:', e)
  }
  renamingId.value = null
}

function cancelRename() {
  renamingId.value = null
}

async function deleteCurrent(e: Event) {
  e.stopPropagation()
  const id = openMenuId.value
  if (!id) return
  try {
    await sessionStore.deleteSession(id)
  } catch (e) {
    console.error('Failed to delete session:', e)
  }
  openMenuId.value = null
}

// 点击会话外部时关闭菜单
function onWrapperClick() {
  closeMenu()
}
</script>

<template>
  <aside
    class="flex h-full w-[268px] shrink-0 flex-col border-r border-white/70 bg-white/46 backdrop-blur-3xl"
    @click="onWrapperClick"
  >
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
        <div
          v-for="session in sortedSessions"
          :key="session.id"
          class="group/session relative"
        >
          <button
            @click="emit('select-session', session.id)"
            class="focus-ring w-full cursor-pointer rounded-[15px] border px-3 py-2.5 text-left transition-[background-color,border-color,box-shadow] duration-200"
            :class="session.id === sessionStore.currentSessionId
              ? 'border-white/90 bg-white/76 shadow-[0_6px_18px_rgba(68,88,117,0.08),inset_0_1px_0_rgba(255,255,255,0.9)]'
              : 'border-transparent hover:border-white/60 hover:bg-white/42'"
          >
            <!-- 重命名模式 -->
            <div v-if="renamingId === session.id" class="flex items-center gap-1.5" @click.stop>
              <input
                v-model="renameValue"
                class="min-w-0 flex-1 rounded-[8px] border border-[var(--primary)]/40 bg-white/80 px-2 py-1 text-[13px] text-[var(--ink)] outline-none focus:border-[var(--primary)]"
                placeholder="会话名称"
                @keydown.enter="confirmRename"
                @keydown.escape="cancelRename"
                ref="renameInput"
              />
              <button
                @click="confirmRename"
                class="shrink-0 rounded-[6px] px-2 py-1 text-[11px] font-medium text-[var(--primary)] hover:bg-[var(--primary)]/10"
              >确定</button>
              <button
                @click="cancelRename"
                class="shrink-0 rounded-[6px] px-1.5 py-1 text-[11px] text-[var(--ink-muted)] hover:bg-black/5"
              >取消</button>
            </div>

            <!-- 正常模式 -->
            <template v-else>
              <div class="flex items-start gap-2.5">
                <span class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-[9px] border border-white/70 bg-white/55 text-[var(--ink-muted)] shadow-sm transition-colors group-hover/session:text-[var(--primary)]">
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
            </template>
          </button>

          <!-- ... 按钮 -->
          <button
            v-if="renamingId !== session.id"
            @click="toggleMenu(session.id, $event)"
            class="absolute right-1.5 top-1.5 z-10 flex h-7 w-7 items-center justify-center rounded-[8px] text-[var(--ink-muted)] opacity-0 transition-all duration-150 hover:bg-black/5 hover:text-[var(--ink)] group-hover/session:opacity-100"
            :class="{ 'opacity-100 bg-black/5': openMenuId === session.id }"
            title="更多操作"
          >
            <MoreHorizontal :size="15" :stroke-width="2" />
          </button>

          <!-- 下拉菜单 -->
          <Teleport to="body">
            <div
              v-if="openMenuId === session.id"
              class="fixed z-[9999] min-w-[140px] rounded-[12px] border border-white/70 bg-white/92 p-1 shadow-[0_12px_40px_rgba(0,0,0,0.12),0_0_0_1px_rgba(0,0,0,0.04)] backdrop-blur-2xl"
              :style="{ left: menuPosition.x + 'px', top: menuPosition.y + 'px' }"
              @click.stop
            >
              <button
                @click="startRename"
                class="flex w-full items-center gap-2 rounded-[8px] px-3 py-2 text-[13px] text-[var(--ink)] transition-colors hover:bg-black/5"
              >
                <Pencil :size="14" :stroke-width="1.8" />
                重命名
              </button>
              <button
                @click="deleteCurrent"
                class="flex w-full items-center gap-2 rounded-[8px] px-3 py-2 text-[13px] text-red-500 transition-colors hover:bg-red-50"
              >
                <Trash2 :size="14" :stroke-width="1.8" />
                删除
              </button>
            </div>
          </Teleport>
        </div>
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
