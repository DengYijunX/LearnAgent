<script setup lang="ts">
import { ref, computed } from 'vue'
import { useChatStore } from '../../stores/chat'
import { useSessionStore } from '../../stores/session'

const emit = defineEmits<{
  (e: 'send', content: string): void
  (e: 'stop'): void
}>()

const chatStore = useChatStore()
const sessionStore = useSessionStore()
const inputValue = ref('')

const canSend = computed(() => {
  return (
    inputValue.value.trim().length > 0 && 
    !chatStore.isProcessing && 
    sessionStore.currentSessionId !== null
  )
})

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    send()
  }
}

function send() {
  if (!canSend.value) return
  emit('send', inputValue.value.trim())
  inputValue.value = ''
}

function stop() {
  emit('stop')
}
</script>

<template>
  <div class="border-t border-[#e8ecf1]/70 px-4 py-3 bg-white/40 backdrop-blur-xl">
    <div class="flex items-end gap-2.5 max-w-3xl mx-auto">
      <div class="flex-1 relative">
        <textarea
          v-model="inputValue"
          @keydown="handleKeydown"
          :disabled="chatStore.isProcessing || !sessionStore.currentSessionId"
          :placeholder="sessionStore.currentSessionId ? '输入问题开始学习...' : '请先点击「新会话」开始'"
          rows="1"
          class="w-full bg-white/80 backdrop-blur-xl text-slate-700 placeholder-slate-400
                 rounded-2xl px-4 py-2.5 pr-10 resize-none
                 focus:outline-none focus:ring-2 focus:ring-[#5b7fff]/30
                 border border-[#e8ecf1]/80 focus:border-[#5b7fff]/40
                 transition-all duration-200 disabled:opacity-40 text-sm"
          style="min-height: 42px; max-height: 160px;"
        />
      </div>

      <button
        v-if="!chatStore.isProcessing"
        @click="send"
        :disabled="!canSend"
        class="shrink-0 w-10 h-10 rounded-full font-medium transition-all duration-200 flex items-center justify-center"
        :class="canSend
          ? 'bg-gradient-to-br from-[#5b7fff] to-[#7c6ff7] text-white shadow-[0_2px_8px_rgba(91,127,255,0.3)] hover:shadow-[0_4px_12px_rgba(91,127,255,0.4)] active:scale-95'
          : 'bg-slate-100 text-slate-400 cursor-not-allowed'"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 2L11 13" /><path d="M22 2l-7 20-4-9-9-4 20-7z" />
        </svg>
      </button>

      <button
        v-else
        @click="stop"
        class="shrink-0 w-10 h-10 rounded-full bg-red-100 text-red-500 hover:bg-red-200 transition-colors flex items-center justify-center"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
          <rect x="7" y="7" width="10" height="10" rx="2" />
        </svg>
      </button>
    </div>

    <!-- 提示信息 -->
    <p class="mt-2 text-xs text-slate-500">
      {{ sessionStore.currentSessionId ? '按 Enter 发送，Shift + Enter 换行' : '请先点击左侧「新会话」按钮创建会话' }}
    </p>
  </div>
</template>
