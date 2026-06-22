<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Layers3 } from 'lucide-vue-next'
import { renderMarkdown } from '../../utils/markdown'
import type { Message } from '../../types/chat'

const props = defineProps<{ message: Message }>()
const bubbleRef = ref<HTMLElement | null>(null)

const renderedContent = computed(() =>
  props.message.role === 'user' ? null : renderMarkdown(props.message.content)
)

const timeStr = computed(() =>
  new Date(props.message.timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit', minute: '2-digit'
  })
)

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
</script>

<template>
  <div v-if="message.role === 'assistant'" class="group flex items-start gap-3.5">
    <div class="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-[11px] bg-[linear-gradient(145deg,#5b93ff,#2867df)] text-white shadow-[0_6px_16px_rgba(47,107,232,0.2)]">
      <Layers3 :size="15" :stroke-width="2.2" />
    </div>
    <div class="min-w-0 flex-1">
      <div class="mb-2 flex items-center gap-2">
        <span class="text-[12px] font-semibold text-[var(--ink)]">LearnAgent</span>
        <span class="text-[10px] tabular-nums text-[var(--ink-muted)]">{{ timeStr }}</span>
      </div>
      <div
        ref="bubbleRef"
        class="overflow-hidden rounded-[18px] border border-white/82 bg-white/76 px-5 py-4 shadow-[0_10px_30px_rgba(59,79,109,0.07),inset_0_1px_0_rgba(255,255,255,0.95)] backdrop-blur-xl
               prose prose-slate prose-sm max-w-none
               prose-headings:font-semibold prose-headings:tracking-[-0.025em] prose-headings:text-[var(--ink)]
               prose-p:leading-7 prose-p:text-[var(--ink-secondary)]
               prose-li:leading-7 prose-li:text-[var(--ink-secondary)]
               prose-strong:text-[var(--ink)]
               prose-pre:m-0 prose-pre:bg-[#f8fafc] prose-pre:shadow-none
               prose-code:bg-[#eef3f8] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:text-[#315071] prose-code:font-normal prose-code:text-[0.88em]
               prose-a:text-[var(--primary)] prose-a:no-underline hover:prose-a:underline"
        v-html="renderedContent"
      />
    </div>
  </div>

  <div v-else class="flex justify-end">
    <div class="max-w-[72%]">
      <div class="rounded-[18px] rounded-tr-[7px] border border-blue-200/55 bg-[linear-gradient(145deg,rgba(227,239,255,0.88),rgba(238,245,255,0.72))] px-4 py-3 text-[14px] leading-6 text-[#27415f] shadow-[0_7px_22px_rgba(55,106,175,0.08),inset_0_1px_0_rgba(255,255,255,0.8)] backdrop-blur-xl whitespace-pre-wrap">
        {{ message.content }}
      </div>
      <p class="mt-1.5 pr-1 text-right text-[10px] tabular-nums text-[var(--ink-muted)]">{{ timeStr }}</p>
    </div>
  </div>
</template>
