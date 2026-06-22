<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { ArrowUpRight, BookOpenText, Code2, GitBranch, Layers3, Sparkles } from 'lucide-vue-next'
import { useChatStore } from '../../stores/chat'
import MessageBubble from './MessageBubble.vue'
import ToolCallCard from './ToolCallCard.vue'

const chatStore = useChatStore()
const containerRef = ref<HTMLElement | null>(null)

const emit = defineEmits<{
  (e: 'select-prompt', prompt: string): void
}>()

const suggestions = [
  {
    icon: BookOpenText,
    eyebrow: '理解概念',
    title: '系统学习一个新主题',
    prompt: '我想系统学习 Python 异步编程，请先了解我的基础并制定学习路径。'
  },
  {
    icon: Code2,
    eyebrow: '动手实践',
    title: '通过小项目边做边学',
    prompt: '带我用一个小项目学习 FastAPI，从需求拆解开始，一步步实践。'
  },
  {
    icon: GitBranch,
    eyebrow: '阅读项目',
    title: '分析仓库并规划阅读顺序',
    prompt: '我想读懂当前代码仓库，请先分析结构，再给我一条循序渐进的阅读路线。'
  }
]

const toolCallEntries = computed(() => Array.from(chatStore.activeToolCalls.entries()))

function scrollToBottom() {
  nextTick(() => {
    if (containerRef.value) containerRef.value.scrollTop = containerRef.value.scrollHeight
  })
}

watch(
  () => [chatStore.messages.length, chatStore.activeToolCalls.size, chatStore.isProcessing],
  scrollToBottom,
  { deep: true }
)

scrollToBottom()
</script>

<template>
  <div ref="containerRef" class="relative flex-1 overflow-y-auto px-7 pb-8 pt-6">
    <div
      v-if="chatStore.messages.length === 0 && !chatStore.isProcessing"
      class="mx-auto flex h-full max-w-[860px] flex-col justify-center py-10"
    >
      <div class="mb-8 flex items-center gap-4">
        <div class="relative flex h-[58px] w-[58px] shrink-0 items-center justify-center rounded-[20px] bg-[linear-gradient(145deg,#5b93ff,#2867df)] text-white shadow-[0_14px_34px_rgba(47,107,232,0.24),inset_0_1px_0_rgba(255,255,255,0.35)]">
          <Layers3 :size="27" :stroke-width="2" />
          <Sparkles :size="13" class="absolute -right-1 -top-1 text-blue-200" />
        </div>
        <div>
          <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--primary)]">LearnAgent workspace</p>
          <h3 class="mt-1 text-[30px] font-semibold tracking-[-0.045em] text-[var(--ink)]">今天想学点什么？</h3>
        </div>
      </div>

      <p class="max-w-[620px] text-[15px] leading-7 text-[var(--ink-secondary)]">
        从一个真实问题开始。我们可以一起发现资料、理解概念、动手实践，再把学到的东西沉淀下来。
      </p>

      <div class="mt-8 grid grid-cols-3 gap-3">
        <button
          v-for="suggestion in suggestions"
          :key="suggestion.title"
          type="button"
          class="focus-ring group cursor-pointer rounded-[18px] border border-white/78 bg-white/52 p-4 text-left shadow-[0_8px_24px_rgba(58,78,108,0.06),inset_0_1px_0_rgba(255,255,255,0.9)] backdrop-blur-xl transition-[background-color,border-color,box-shadow] duration-200 hover:border-blue-200/80 hover:bg-white/76 hover:shadow-[0_12px_30px_rgba(58,78,108,0.1)]"
          @click="emit('select-prompt', suggestion.prompt)"
        >
          <div class="mb-5 flex items-center justify-between">
            <span class="flex h-9 w-9 items-center justify-center rounded-[12px] bg-blue-50 text-[var(--primary)]">
              <component :is="suggestion.icon" :size="17" />
            </span>
            <ArrowUpRight :size="15" class="text-[var(--ink-muted)] transition-colors group-hover:text-[var(--primary)]" />
          </div>
          <p class="text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--ink-muted)]">{{ suggestion.eyebrow }}</p>
          <p class="mt-1.5 text-[13px] font-semibold leading-5 text-[var(--ink)]">{{ suggestion.title }}</p>
        </button>
      </div>
    </div>

    <div v-else class="mx-auto max-w-[860px] space-y-6">
      <div v-for="message in chatStore.messages" :key="message.id" class="animate-fadeIn">
        <ToolCallCard
          v-if="message.role === 'tool' && message.toolCallId"
          v-for="[id, toolCall] in toolCallEntries"
          :key="id"
          v-show="toolCall.id === message.toolCallId"
          :tool-call="toolCall"
        />
        <MessageBubble v-else-if="message.role !== 'tool'" :message="message" />
      </div>

      <div
        v-if="chatStore.isProcessing && chatStore.messages.length > 0"
        class="flex items-center gap-3 rounded-[16px] border border-white/70 bg-white/42 px-4 py-3 text-[var(--ink-secondary)] backdrop-blur-xl"
      >
        <div class="flex gap-1">
          <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-400" style="animation-delay: 0ms" />
          <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-500" style="animation-delay: 150ms" />
          <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-blue-600" style="animation-delay: 300ms" />
        </div>
        <span class="text-[12px] font-medium">LearnAgent 正在组织下一步…</span>
      </div>
    </div>
  </div>
</template>
