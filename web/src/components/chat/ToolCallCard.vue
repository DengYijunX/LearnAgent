<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ToolCallState } from '../../types/chat'

const props = defineProps<{
  toolCall: ToolCallState
}>()

const isExpanded = ref(false)

const statusIcon = computed(() => {
  switch (props.toolCall.status) {
    case 'running':
      return '⏳'
    case 'done':
      return '✅'
    case 'error':
      return '❌'
    default:
      return '❓'
  }
})

const borderColor = computed(() => {
  switch (props.toolCall.status) {
    case 'running':
      return 'border-amber-500/50'
    case 'done':
      return 'border-emerald-500/50'
    case 'error':
      return 'border-red-500/50'
    default:
      return 'border-slate-600'
  }
})

const elapsedText = computed(() => {
  if (props.toolCall.elapsed === undefined) return ''
  if (props.toolCall.elapsed < 1) return `${(props.toolCall.elapsed * 1000).toFixed(0)}ms`
  return `${props.toolCall.elapsed.toFixed(1)}s`
})

function toggleExpand() {
  if (props.toolCall.status !== 'running') {
    isExpanded.value = !isExpanded.value
  }
}
</script>

<template>
  <div
    class="rounded-lg overflow-hidden transition-all duration-200"
    :class="[
      'bg-slate-900 border-l-4',
      borderColor
    ]"
  >
    <!-- 头部：工具名称和状态 -->
    <div
      @click="toggleExpand"
      class="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-slate-800/50"
      :class="{ 'cursor-default': toolCall.status === 'running' }"
    >
      <div class="flex items-center gap-3">
        <span class="text-lg">{{ statusIcon }}</span>
        <div>
          <p class="text-sm font-medium text-slate-200">
            {{ toolCall.name }}
          </p>
          <p class="text-xs text-slate-400 mt-0.5">
            {{ toolCall.description }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <!-- 耗时 -->
        <span
          v-if="elapsedText"
          class="text-xs px-2 py-1 rounded bg-slate-800 text-slate-400"
        >
          {{ elapsedText }}
        </span>

        <!-- 展开/收起图标 -->
        <svg
          v-if="toolCall.status !== 'running'"
          class="w-4 h-4 text-slate-500 transition-transform"
          :class="{ 'rotate-180': isExpanded }"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>

    <!-- 展开内容 -->
    <div
      v-if="isExpanded && toolCall.status !== 'running'"
      class="px-4 pb-4 border-t border-slate-800"
    >
      <!-- 结果摘要 -->
      <div
        v-if="toolCall.resultSummary"
        class="mt-3 text-sm text-slate-300 whitespace-pre-wrap"
      >
        {{ toolCall.resultSummary }}
      </div>

      <!-- 搜索结果标题列表 -->
      <div
        v-if="toolCall.resultTitles && toolCall.resultTitles.length > 0"
        class="mt-3 space-y-2"
      >
        <p class="text-xs text-slate-500 uppercase tracking-wider">搜索结果</p>
        <ul class="space-y-1">
          <li
            v-for="(title, index) in toolCall.resultTitles"
            :key="index"
            class="text-sm text-slate-300 flex items-start gap-2"
          >
            <span class="text-slate-500">{{ index + 1 }}.</span>
            <span>{{ title }}</span>
          </li>
        </ul>
      </div>

      <!-- 输入参数 -->
      <div class="mt-3">
        <p class="text-xs text-slate-500 uppercase tracking-wider mb-1">输入参数</p>
        <pre class="text-xs text-slate-400 bg-slate-950 p-2 rounded overflow-x-auto">{{ JSON.stringify(toolCall.input, null, 2) }}</pre>
      </div>
    </div>

    <!-- 运行中动画 -->
    <div
      v-if="toolCall.status === 'running'"
      class="px-4 pb-3"
    >
      <div class="flex items-center gap-2 mt-2">
        <div class="flex gap-1">
          <span class="w-1.5 h-1.5 bg-amber-500 rounded-full animate-bounce" style="animation-delay: 0ms" />
          <span class="w-1.5 h-1.5 bg-amber-500 rounded-full animate-bounce" style="animation-delay: 150ms" />
          <span class="w-1.5 h-1.5 bg-amber-500 rounded-full animate-bounce" style="animation-delay: 300ms" />
        </div>
        <span class="text-xs text-slate-500">执行中...</span>
      </div>
    </div>
  </div>
</template>
