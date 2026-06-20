<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { ArrowUp, CornerDownLeft, Square } from 'lucide-vue-next'
import { useChatStore } from '../../stores/chat'
import { useSessionStore } from '../../stores/session'

const emit = defineEmits<{
  (e: 'send', content: string): void
  (e: 'stop'): void
}>()

const chatStore = useChatStore()
const sessionStore = useSessionStore()
const inputValue = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const canSend = computed(() =>
  inputValue.value.trim().length > 0 &&
  !chatStore.isProcessing &&
  sessionStore.currentSessionId !== null
)

function resizeTextarea() {
  const textarea = textareaRef.value
  if (!textarea) return
  textarea.style.height = 'auto'
  textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`
}

function send() {
  if (!canSend.value) return
  emit('send', inputValue.value.trim())
  inputValue.value = ''
  nextTick(resizeTextarea)
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    send()
  }
}

function setDraft(content: string) {
  inputValue.value = content
  nextTick(() => {
    resizeTextarea()
    textareaRef.value?.focus()
    textareaRef.value?.setSelectionRange(content.length, content.length)
  })
}

defineExpose({ setDraft })
</script>

<template>
  <div class="relative z-20 shrink-0 px-7 pb-5 pt-2">
    <div class="glass-panel mx-auto max-w-[860px] rounded-[21px] p-2.5">
      <div class="flex items-end gap-2.5">
        <textarea
          ref="textareaRef"
          v-model="inputValue"
          :disabled="chatStore.isProcessing || !sessionStore.currentSessionId"
          :placeholder="sessionStore.currentSessionId ? '继续提问，或描述你想动手实践的内容…' : '请先创建一个会话'"
          rows="1"
          aria-label="会话输入"
          class="min-h-[48px] max-h-40 w-full resize-none overflow-y-auto rounded-[15px] border border-transparent bg-transparent px-3.5 py-3 text-[14px] leading-6 text-[var(--ink)] placeholder:text-[var(--ink-muted)] focus:border-blue-100 focus:bg-white/45 focus:outline-none disabled:cursor-not-allowed disabled:opacity-45"
          @keydown="handleKeydown"
          @input="resizeTextarea"
        />

        <button
          v-if="!chatStore.isProcessing"
          type="button"
          :disabled="!canSend"
          aria-label="发送消息"
          class="focus-ring flex h-10 w-10 shrink-0 items-center justify-center rounded-[13px] transition-[background-color,box-shadow] duration-200"
          :class="canSend
            ? 'cursor-pointer bg-[linear-gradient(145deg,#4c88fb,#2d6be7)] text-white shadow-[0_7px_18px_rgba(47,107,232,0.24)] hover:shadow-[0_9px_22px_rgba(47,107,232,0.32)]'
            : 'cursor-not-allowed bg-slate-100/80 text-slate-400'"
          @click="send"
        >
          <ArrowUp :size="18" :stroke-width="2.3" />
        </button>

        <button
          v-else
          type="button"
          aria-label="停止生成"
          class="focus-ring flex h-10 w-10 shrink-0 cursor-pointer items-center justify-center rounded-[13px] bg-red-50 text-red-600 transition-colors hover:bg-red-100"
          @click="emit('stop')"
        >
          <Square :size="16" fill="currentColor" />
        </button>
      </div>

      <div class="flex items-center justify-between px-3 pb-1 pt-1.5 text-[10px] text-[var(--ink-muted)]">
        <span>{{ sessionStore.currentSessionId ? 'LearnAgent 也可能犯错，请核对重要信息。' : '点击左侧「新建会话」开始。' }}</span>
        <span v-if="sessionStore.currentSessionId" class="flex items-center gap-1.5">
          <CornerDownLeft :size="11" />
          Enter 发送 · Shift + Enter 换行
        </span>
      </div>
    </div>
  </div>
</template>
