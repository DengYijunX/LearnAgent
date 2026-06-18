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
  <div class="border-t border-slate-700 p-4 bg-slate-900">
    <div class="flex items-end gap-3">
      <!-- 输入框 -->
      <div class="flex-1 relative">
        <textarea
          v-model="inputValue"
          @keydown="handleKeydown"
          :disabled="chatStore.isProcessing || !sessionStore.currentSessionId"
          :placeholder="sessionStore.currentSessionId ? '输入问题开始学习...' : '请先点击「新会话」开始'"
          rows="1"
          class="w-full bg-slate-800 text-white placeholder-slate-500 rounded-lg px-4 py-3 pr-12 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/50 border border-slate-700 focus:border-blue-500 transition-colors disabled:opacity-50"
          style="min-height: 48px; max-height: 200px;"
        />
      </div>

      <!-- 发送/停止按钮 -->
      <button
        v-if="!chatStore.isProcessing"
        @click="send"
        :disabled="!canSend"
        class="px-4 py-3 rounded-lg font-medium transition-all flex items-center gap-2"
        :class="[
          canSend
            ? 'bg-blue-600 hover:bg-blue-500 text-white'
            : 'bg-slate-700 text-slate-500 cursor-not-allowed'
        ]"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 2L11 13" />
          <path d="M22 2l-7 20-4-9-9-4 20-7z" />
        </svg>
        <span class="hidden sm:inline">发送</span>
      </button>

      <button
        v-else
        @click="stop"
        class="px-4 py-3 rounded-lg font-medium bg-red-600 hover:bg-red-500 text-white transition-colors flex items-center gap-2"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="6" width="12" height="12" rx="2" />
        </svg>
        <span class="hidden sm:inline">停止</span>
      </button>
    </div>

    <!-- 提示信息 -->
    <p class="mt-2 text-xs text-slate-500">
      {{ sessionStore.currentSessionId ? '按 Enter 发送，Shift + Enter 换行' : '请先点击左侧「新会话」按钮创建会话' }}
    </p>
  </div>
</template>
