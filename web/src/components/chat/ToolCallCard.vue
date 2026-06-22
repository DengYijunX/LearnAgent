<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  ChevronDown, CircleCheck, CircleX, FileText, FolderOpen, Github, Globe,
  LoaderCircle, Search, Terminal, Wrench
} from 'lucide-vue-next'
import type { ToolCallState } from '../../types/chat'

const props = defineProps<{ toolCall: ToolCallState }>()
const isExpanded = ref(false)

const status = computed(() => {
  if (props.toolCall.status === 'running') {
    return { icon: LoaderCircle, label: '执行中', tone: 'text-blue-700', rail: 'bg-blue-500', surface: 'bg-blue-50/58 border-blue-100/80' }
  }
  if (props.toolCall.status === 'done') {
    return { icon: CircleCheck, label: '已完成', tone: 'text-emerald-700', rail: 'bg-emerald-500', surface: 'bg-emerald-50/42 border-emerald-100/80' }
  }
  return { icon: CircleX, label: '执行失败', tone: 'text-red-700', rail: 'bg-red-500', surface: 'bg-red-50/48 border-red-100/80' }
})

const toolIcon = computed(() => {
  const name = props.toolCall.name.toLowerCase()
  if (name.includes('search')) return Search
  if (name.includes('url') || name.includes('web')) return Globe
  if (name.includes('github') || name.includes('repo')) return Github
  if (name.includes('file') || name.includes('read')) return FileText
  if (name.includes('workspace') || name.includes('folder')) return FolderOpen
  if (name.includes('code') || name.includes('command') || name.includes('run')) return Terminal
  return Wrench
})

const elapsedText = computed(() => {
  if (props.toolCall.elapsed === undefined) return ''
  if (props.toolCall.elapsed < 1) return `${(props.toolCall.elapsed * 1000).toFixed(0)}ms`
  return `${props.toolCall.elapsed.toFixed(1)}s`
})

function toggleExpand() {
  if (props.toolCall.status !== 'running') isExpanded.value = !isExpanded.value
}
</script>

<template>
  <div class="relative ml-[46px] overflow-hidden rounded-[17px] border bg-white/62 shadow-[0_8px_24px_rgba(59,79,109,0.055),inset_0_1px_0_rgba(255,255,255,0.9)] backdrop-blur-xl" :class="status.surface">
    <span class="absolute bottom-3 left-0 top-3 w-[3px] rounded-r-full" :class="status.rail" aria-hidden="true" />

    <button
      type="button"
      class="focus-ring flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors duration-200"
      :class="toolCall.status === 'running' ? 'cursor-default' : 'cursor-pointer hover:bg-white/48'"
      :aria-expanded="toolCall.status === 'running' ? undefined : isExpanded"
      @click="toggleExpand"
    >
      <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-[12px] border border-white/80 bg-white/68 text-[var(--primary)] shadow-sm">
        <component :is="toolIcon" :size="17" />
      </span>

      <span class="min-w-0 flex-1">
        <span class="flex items-center gap-2">
          <span class="truncate text-[13px] font-semibold text-[var(--ink)]">{{ toolCall.name }}</span>
          <span class="flex items-center gap-1 text-[10px] font-semibold" :class="status.tone">
            <component :is="status.icon" :size="12" :class="{ 'animate-spin': toolCall.status === 'running' }" />
            {{ status.label }}
          </span>
        </span>
        <span class="mt-1 block truncate text-[11px] text-[var(--ink-muted)]">{{ toolCall.description }}</span>
      </span>

      <span v-if="elapsedText" class="rounded-lg border border-white/75 bg-white/54 px-2 py-1 text-[10px] tabular-nums text-[var(--ink-muted)]">{{ elapsedText }}</span>
      <ChevronDown
        v-if="toolCall.status !== 'running'"
        :size="15"
        class="text-[var(--ink-muted)] transition-transform duration-200"
        :class="{ 'rotate-180': isExpanded }"
      />
    </button>

    <div v-if="isExpanded && toolCall.status !== 'running'" class="border-t border-[var(--line)] px-4 pb-4 pt-3">
      <p v-if="toolCall.resultSummary" class="whitespace-pre-wrap text-[12px] leading-6 text-[var(--ink-secondary)]">{{ toolCall.resultSummary }}</p>

      <div v-if="toolCall.resultTitles?.length" class="mt-3 rounded-[13px] border border-white/76 bg-white/48 p-3">
        <p class="mb-2 text-[10px] font-semibold uppercase tracking-[0.13em] text-[var(--ink-muted)]">结果摘要</p>
        <ol class="space-y-1.5">
          <li v-for="(title, index) in toolCall.resultTitles" :key="index" class="flex gap-2 text-[12px] leading-5 text-[var(--ink-secondary)]">
            <span class="font-medium tabular-nums text-[var(--primary)]">{{ index + 1 }}.</span>
            <span>{{ title }}</span>
          </li>
        </ol>
      </div>

      <details class="mt-3">
        <summary class="cursor-pointer text-[10px] font-semibold uppercase tracking-[0.13em] text-[var(--ink-muted)]">输入参数</summary>
        <pre class="mt-2 max-h-56 overflow-auto rounded-[12px] border border-[var(--line)] bg-[#f7f9fc] p-3 text-[11px] leading-5 text-[#496078]">{{ JSON.stringify(toolCall.input, null, 2) }}</pre>
      </details>
    </div>
  </div>
</template>
