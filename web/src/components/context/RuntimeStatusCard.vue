<script setup lang="ts">
import { computed } from 'vue'
import { Activity, Square, Terminal, Wrench } from 'lucide-vue-next'
import type { RuntimeProcess } from '../../types/api'
import type { ToolCallState } from '../../types/chat'

const props = defineProps<{
  processes: RuntimeProcess[]
  toolCalls: ToolCallState[]
  toolCount: number
  error?: string
}>()

const emit = defineEmits<{ (e: 'stop-process', process: RuntimeProcess): void }>()
const runningTools = computed(() => props.toolCalls.filter(tool => tool.status === 'running'))
function elapsed(seconds: number) {
  if (seconds < 60) return `${Math.max(0, Math.round(seconds))} 秒`
  return `${Math.floor(seconds / 60)} 分`
}
</script>

<template>
  <section class="context-card" aria-labelledby="runtime-card-title">
    <div class="context-card-title-row">
      <div class="flex items-center gap-2">
        <span class="context-card-icon bg-cyan-50 text-cyan-700"><Activity :size="15" /></span>
        <h3 id="runtime-card-title" class="context-card-title">运行状态</h3>
      </div>
      <span class="text-[10px] text-[var(--ink-muted)]">{{ toolCount }} 个工具</span>
    </div>

    <p v-if="error" class="context-error">{{ error }}</p>
    <div v-if="runningTools.length" class="mt-3 space-y-2">
      <div v-for="tool in runningTools" :key="tool.id" class="flex items-start gap-2 rounded-[10px] bg-blue-50/65 px-2.5 py-2">
        <Wrench :size="13" class="mt-0.5 shrink-0 animate-pulse text-blue-600" />
        <div class="min-w-0">
          <p class="truncate text-[10px] font-semibold text-blue-800">{{ tool.name }}</p>
          <p class="mt-0.5 line-clamp-2 text-[10px] leading-4 text-blue-700/70">{{ tool.description }}</p>
        </div>
      </div>
    </div>

    <div v-if="processes.length" class="mt-3 space-y-2">
      <div v-for="process in processes" :key="process.pid" class="rounded-[11px] border border-white/75 bg-white/48 px-2.5 py-2">
        <div class="flex items-center gap-2">
          <Terminal :size="13" class="shrink-0 text-slate-500" />
          <code class="min-w-0 flex-1 truncate text-[10px] text-[var(--ink-secondary)]">{{ process.command }}</code>
          <button type="button" class="context-icon-button text-red-600" :aria-label="`停止进程 ${process.pid}`" @click="emit('stop-process', process)"><Square :size="11" fill="currentColor" /></button>
        </div>
        <p class="mt-1 pl-5 text-[9px] text-[var(--ink-muted)]">PID {{ process.pid }} · {{ elapsed(process.elapsed) }}<template v-if="process.port"> · 端口 {{ process.port }}</template></p>
      </div>
    </div>
    <p v-if="!error && !processes.length && !runningTools.length" class="context-empty">当前没有运行中的工具或后台进程</p>
  </section>
</template>
