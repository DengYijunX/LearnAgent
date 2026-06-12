<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useChatStore } from '../../stores/chat'

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'deny'): void
}>()

const chatStore = useChatStore()
const rememberChoice = ref(false)

// 工具图标
const toolIcon = computed(() => {
  const name = chatStore.pendingPermission?.toolName || ''
  switch (name) {
    case 'file_write':
    case 'file_read':
      return '📄'
    case 'search_web':
      return '🔍'
    case 'run_code':
    case 'execute_command':
      return '⚡'
    case 'read_url':
      return '🌐'
    default:
      return '🔧'
  }
})

// 工具名称中文
const toolNameCN = computed(() => {
  const name = chatStore.pendingPermission?.toolName || ''
  switch (name) {
    case 'file_write':
      return '写入文件'
    case 'file_read':
      return '读取文件'
    case 'search_web':
      return '搜索网页'
    case 'run_code':
      return '运行代码'
    case 'execute_command':
      return '执行命令'
    case 'read_url':
      return '读取网页'
    default:
      return name
  }
})

// 参数预览
const inputPreview = computed(() => {
  if (!chatStore.pendingPermission?.toolInput) return ''
  const input = chatStore.pendingPermission.toolInput

  // 针对不同工具优化展示
  if (input.path) {
    return `路径: ${input.path}`
  }
  if (input.url) {
    return `URL: ${input.url}`
  }
  if (input.query) {
    return `查询: ${input.query}`
  }
  if (input.command) {
    return `命令: ${input.command}`
  }

  // 通用 JSON 展示
  return JSON.stringify(input, null, 2).substring(0, 200)
})

// 内容预览（如果有）
const contentPreview = computed(() => {
  if (!chatStore.pendingPermission?.toolInput) return ''
  const input = chatStore.pendingPermission.toolInput
  if (input.content && typeof input.content === 'string') {
    const content = input.content as string
    return content.length > 100 ? content.substring(0, 100) + '...' : content
  }
  return ''
})

watch(rememberChoice, (val) => {
  if (val) {
    // 60秒免确认逻辑可以在此处处理
    console.log('Remember choice for 60s')
  }
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="chatStore.hasPendingPermission"
      class="fixed inset-0 z-50 flex items-center justify-center"
    >
      <!-- 背景遮罩 -->
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      <!-- 弹窗 -->
      <div class="relative bg-slate-800 rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        <!-- 头部 -->
        <div class="px-6 py-4 border-b border-slate-700 flex items-center gap-3">
          <span class="text-2xl">{{ toolIcon }}</span>
          <div>
            <h3 class="text-lg font-medium text-white">{{ toolNameCN }}</h3>
            <p class="text-sm text-slate-400">需要您的确认才能继续</p>
          </div>
        </div>

        <!-- 内容 -->
        <div class="px-6 py-4 space-y-4">
          <!-- 原因 -->
          <div>
            <p class="text-sm text-slate-300">
              {{ chatStore.pendingPermission?.reason }}
            </p>
          </div>

          <!-- 参数预览 -->
          <div class="bg-slate-900 rounded-lg p-3">
            <p class="text-xs text-slate-500 uppercase tracking-wider mb-1">参数预览</p>
            <p class="text-sm text-slate-300 font-mono">{{ inputPreview }}</p>
            <p
              v-if="contentPreview"
              class="text-sm text-slate-400 mt-2 border-t border-slate-700 pt-2"
            >
              {{ contentPreview }}
            </p>
          </div>

          <!-- 免确认选项 -->
          <label class="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
            <input
              v-model="rememberChoice"
              type="checkbox"
              class="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-800"
            />
            <span>同类操作 60 秒内免确认</span>
          </label>
        </div>

        <!-- 底部按钮 -->
        <div class="px-6 py-4 bg-slate-900/50 flex items-center justify-end gap-3">
          <button
            @click="emit('deny')"
            class="px-4 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-700 transition-colors"
          >
            拒绝
          </button>
          <button
            @click="emit('confirm')"
            class="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors"
          >
            允许
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
