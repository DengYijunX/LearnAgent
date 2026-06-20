<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { renderMarkdown } from '../../utils/markdown'
import type { Message } from '../../types/chat'

const props = defineProps<{
  message: Message
}>()

const renderedContent = computed(() => {
  if (props.message.role === 'user') return null
  return renderMarkdown(props.message.content)
})

const bubbleRef = ref<HTMLElement | null>(null)

// 代码块复制按钮事件委托 + 渲染结果注入
onMounted(() => {
  const el = bubbleRef.value
  if (!el) return
  el.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const code = (btn as HTMLElement).getAttribute('data-code') || ''
      navigator.clipboard.writeText(code).then(() => {
        btn.textContent = '已复制'
        setTimeout(() => { btn.textContent = '复制' }, 1500)
      })
    })
  })
})

const timeStr = computed(() =>
  new Date(props.message.timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit', minute: '2-digit'
  })
)
</script>

<template>
  <div class="flex" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
    <!-- 助手消息：白底卡片 + 微阴影 -->
    <div
      v-if="message.role === 'assistant'"
      ref="bubbleRef"
      class="max-w-[80%] bg-white/[0.85] backdrop-blur-xl rounded-2xl px-5 py-3.5
             shadow-[0_1px_3px_rgba(0,0,0,0.04),0_4px_16px_rgba(0,0,0,0.03)]
             border border-white/80
             prose prose-slate prose-sm max-w-none
             prose-headings:font-semibold prose-headings:tracking-tight
             prose-pre:bg-[#f8f9fc] prose-pre:shadow-none prose-pre:border prose-pre:border-[#e8ecf1]
             prose-code:bg-[#f0f3f8] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:text-[#334155] prose-code:font-normal prose-code:text-[0.88em]
             prose-a:text-[#5b7fff] prose-a:no-underline hover:prose-a:underline"
      v-html="renderedContent"
    />

    <!-- 用户消息：浅蓝气泡 -->
    <div
      v-else
      class="max-w-[75%] bg-gradient-to-br from-[#5b7fff]/12 to-[#8b5cf6]/08
             backdrop-blur-md rounded-2xl px-4 py-2.5
             border border-[#5b7fff]/15
             text-slate-700 whitespace-pre-wrap text-[0.92rem] leading-relaxed"
    >
      {{ message.content }}
    </div>

    <span
      class="text-[0.7rem] text-slate-400/70 mt-1 px-1"
      :class="message.role === 'user' ? 'order-first' : ''"
    >{{ timeStr }}</span>
  </div>
</template>
