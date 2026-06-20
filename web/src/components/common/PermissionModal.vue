<script setup lang="ts">
import { computed } from 'vue'
import { Check, FileText, Globe, Search, ShieldAlert, Terminal, Wrench, X } from 'lucide-vue-next'
import { useChatStore } from '../../stores/chat'

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'deny'): void
}>()

const chatStore = useChatStore()

const toolIcon = computed(() => {
  const name = chatStore.pendingPermission?.toolName || ''
  if (name === 'file_write' || name === 'file_read') return FileText
  if (name === 'search_web') return Search
  if (name === 'run_code' || name === 'execute_command') return Terminal
  if (name === 'read_url') return Globe
  return Wrench
})

const toolNameCN = computed(() => {
  const names: Record<string, string> = {
    file_write: '写入文件',
    file_read: '读取文件',
    search_web: '搜索网页',
    run_code: '运行代码',
    execute_command: '执行命令',
    read_url: '读取网页'
  }
  const name = chatStore.pendingPermission?.toolName || ''
  return names[name] || name
})

const inputPreview = computed(() => {
  const input = chatStore.pendingPermission?.toolInput
  if (!input) return ''
  if (input.path) return `路径：${input.path}`
  if (input.url) return `URL：${input.url}`
  if (input.query) return `查询：${input.query}`
  if (input.command) return `命令：${input.command}`
  return JSON.stringify(input, null, 2).substring(0, 240)
})

const contentPreview = computed(() => {
  const content = chatStore.pendingPermission?.toolInput?.content
  if (typeof content !== 'string') return ''
  return content.length > 180 ? `${content.substring(0, 180)}…` : content
})
</script>

<template>
  <Teleport to="body">
    <div v-if="chatStore.hasPendingPermission" class="fixed inset-0 z-50 flex items-center justify-center p-6">
      <div class="absolute inset-0 bg-[#24334b]/30 backdrop-blur-[8px]" aria-hidden="true" />

      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="permission-title"
        class="glass-panel relative w-full max-w-[480px] overflow-hidden rounded-[24px] border-white/80 bg-white/88 shadow-[0_30px_90px_rgba(35,49,70,0.22),inset_0_1px_0_rgba(255,255,255,0.95)]"
      >
        <div class="flex items-start gap-4 border-b border-[var(--line)] px-6 py-5">
          <div class="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-[15px] border border-amber-200/70 bg-amber-50 text-amber-700">
            <component :is="toolIcon" :size="20" />
            <ShieldAlert :size="12" class="absolute -bottom-1 -right-1 rounded-full bg-white text-amber-600" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-[10px] font-semibold uppercase tracking-[0.16em] text-amber-700">需要你的确认</p>
            <h2 id="permission-title" class="mt-1 text-[18px] font-semibold tracking-[-0.025em] text-[var(--ink)]">允许 LearnAgent {{ toolNameCN }}？</h2>
            <p class="mt-1 text-[12px] leading-5 text-[var(--ink-muted)]">执行前请确认目标和参数符合你的预期。</p>
          </div>
        </div>

        <div class="space-y-4 px-6 py-5">
          <div>
            <p class="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--ink-muted)]">请求原因</p>
            <p class="mt-2 text-[13px] leading-6 text-[var(--ink-secondary)]">{{ chatStore.pendingPermission?.reason }}</p>
          </div>

          <div class="rounded-[16px] border border-[var(--line)] bg-[#f7f9fc] p-4">
            <p class="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--ink-muted)]">参数预览</p>
            <pre class="mt-2 whitespace-pre-wrap break-all font-mono text-[12px] leading-5 text-[#425a74]">{{ inputPreview }}</pre>
            <p v-if="contentPreview" class="mt-3 border-t border-[var(--line)] pt-3 text-[12px] leading-5 text-[var(--ink-secondary)]">{{ contentPreview }}</p>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2.5 border-t border-[var(--line)] bg-white/46 px-6 py-4">
          <button
            type="button"
            class="focus-ring flex cursor-pointer items-center gap-2 rounded-[12px] px-4 py-2.5 text-[12px] font-semibold text-[var(--ink-secondary)] transition-colors hover:bg-slate-100/80"
            @click="emit('deny')"
          >
            <X :size="14" />
            拒绝
          </button>
          <button
            type="button"
            class="focus-ring flex cursor-pointer items-center gap-2 rounded-[12px] bg-[linear-gradient(145deg,#4b86fb,#2e6be8)] px-4 py-2.5 text-[12px] font-semibold text-white shadow-[0_7px_18px_rgba(46,107,232,0.22)] transition-shadow hover:shadow-[0_9px_22px_rgba(46,107,232,0.3)]"
            @click="emit('confirm')"
          >
            <Check :size="14" />
            允许一次
          </button>
        </div>
      </section>
    </div>
  </Teleport>
</template>
