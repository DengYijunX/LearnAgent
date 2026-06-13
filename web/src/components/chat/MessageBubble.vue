<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import type { Message } from '../../types/chat'

const props = defineProps<{
  message: Message
}>()

// 配置 marked
marked.setOptions({
  gfm: true,
  breaks: true
})

const renderedContent = computed(() => {
  if (props.message.role === 'user') {
    return escapeHtml(props.message.content)
  }
  const html = marked(props.message.content) as string
  return DOMPurify.sanitize(html)
})

function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

const bubbleClasses = computed(() => {
  switch (props.message.role) {
    case 'user':
      return 'bg-blue-600 text-white ml-auto'
    case 'assistant':
      return 'bg-slate-800 text-slate-100'
    case 'tool':
      return props.message.isError
        ? 'bg-slate-900 border-l-4 border-red-500 text-slate-300'
        : 'bg-slate-900 border-l-4 border-slate-600 text-slate-300'
    default:
      return 'bg-slate-800 text-slate-100'
  }
})

const alignmentClass = computed(() => {
  return props.message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
})
</script>

<template>
  <div class="flex" :class="alignmentClass">
    <div
      class="max-w-[75%] rounded-lg px-4 py-2"
      :class="bubbleClasses"
    >
      <!-- 用户消息：纯文本 -->
      <div v-if="message.role === 'user'" class="whitespace-pre-wrap">
        {{ message.content }}
      </div>

      <!-- 助手消息：Markdown -->
      <div
        v-else-if="message.role === 'assistant'"
        class="prose prose-invert prose-sm max-w-none"
        v-html="renderedContent"
      />

      <!-- 工具消息：代码块样式 -->
      <div v-else class="font-mono text-sm whitespace-pre-wrap">
        {{ message.content }}
      </div>

      <!-- 时间戳 -->
      <div
        v-if="message.role !== 'tool'"
        class="text-xs mt-1 opacity-60"
        :class="message.role === 'user' ? 'text-blue-200' : 'text-slate-400'"
      >
        {{ new Date(message.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}
      </div>
    </div>
  </div>
</template>
