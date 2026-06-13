<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { useChatStore } from '../../stores/chat'
import MessageBubble from './MessageBubble.vue'
import ToolCallCard from './ToolCallCard.vue'

const chatStore = useChatStore()
const containerRef = ref<HTMLElement | null>(null)

// 过滤出工具调用卡片
const toolCallEntries = computed(() => {
  return Array.from(chatStore.activeToolCalls.entries())
})

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (containerRef.value) {
      containerRef.value.scrollTop = containerRef.value.scrollHeight
    }
  })
}

// 监听消息变化自动滚动
watch(
  () => [
    chatStore.messages.length,
    chatStore.activeToolCalls.size,
    chatStore.isProcessing
  ],
  () => {
    scrollToBottom()
  },
  { deep: true }
)

// 初始滚动
scrollToBottom()
</script>

<template>
  <div
    ref="containerRef"
    class="flex-1 overflow-y-auto p-4 space-y-4"
  >
    <!-- 欢迎消息 -->
    <div
      v-if="chatStore.messages.length === 0 && !chatStore.isProcessing"
      class="flex flex-col items-center justify-center h-full text-center"
    >
      <div class="w-16 h-16 mb-4 rounded-full bg-slate-800 flex items-center justify-center">
        <svg class="w-8 h-8 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
      </div>
      <h3 class="text-lg font-medium text-slate-200 mb-2">开始学习</h3>
      <p class="text-sm text-slate-500 max-w-md">
        输入你想学习的主题，比如"Python 基础"、"React 框架"或"如何设计 API"，我会帮你系统性地学习和掌握。
      </p>
    </div>

    <!-- 消息列表 -->
    <template v-else>
      <div
        v-for="message in chatStore.messages"
        :key="message.id"
        class="animate-fadeIn"
      >
        <!-- 工具消息不显示气泡，而是显示卡片 -->
        <ToolCallCard
          v-if="message.role === 'tool' && message.toolCallId"
          v-for="[id, toolCall] in toolCallEntries"
          :key="id"
          v-show="toolCall.id === message.toolCallId"
          :toolCall="toolCall"
        />

        <!-- 普通消息显示气泡 -->
        <MessageBubble
          v-else-if="message.role !== 'tool'"
          :message="message"
        />
      </div>
    </template>

    <!-- 处理中指示器 -->
    <div
      v-if="chatStore.isProcessing && chatStore.messages.length > 0"
      class="flex items-center gap-3 text-slate-400"
    >
      <div class="flex gap-1">
        <span class="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style="animation-delay: 0ms" />
        <span class="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style="animation-delay: 150ms" />
        <span class="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style="animation-delay: 300ms" />
      </div>
      <span class="text-sm">Agent 正在思考...</span>
    </div>
  </div>
</template>

<style scoped>
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fadeIn {
  animation: fadeIn 0.15s ease-out;
}
</style>
