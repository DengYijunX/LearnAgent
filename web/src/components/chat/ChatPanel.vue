<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import AppHeader from '../layout/AppHeader.vue'
import MessageList from './MessageList.vue'
import ChatInput from './ChatInput.vue'
import PermissionModal from '../common/PermissionModal.vue'
import { useChatStore } from '../../stores/chat'
import { useSessionStore } from '../../stores/session'
import { useWebSocket } from '../../composables/useWebSocket'

const chatStore = useChatStore()
const sessionStore = useSessionStore()
const {
  connect,
  disconnect,
  sendChat,
  sendPermissionResponse,
  sendCancel,
  sendSetMode,
  isConnecting
} = useWebSocket()

const emit = defineEmits<{
  (e: 'disconnected'): void
}>()

// 初始化
onMounted(async () => {
  await sessionStore.loadSessions()
  if (sessionStore.sessions.length > 0) {
    // 自动连接最近的会话
    const latestSession = sessionStore.sessions[0]
    await selectSession(latestSession.id)
  }
})

// 监听当前会话变化
watch(
  () => sessionStore.currentSessionId,
  async (newId) => {
    if (newId) {
      connect(newId)
    } else {
      disconnect()
    }
  }
)

// 选择会话
async function selectSession(id: string) {
  if (sessionStore.currentSessionId === id) return

  disconnect()
  sessionStore.setCurrentSession(id)

  // 加载会话详情
  try {
    const { sessionApi } = await import('../../api/client')
    const detail = await sessionApi.getSession(id)

    // 恢复消息
    chatStore.clearMessages()
    detail.messages.forEach(msg => {
      chatStore.addMessage({
        id: Math.random().toString(36).substring(2, 10),
        role: msg.role as 'user' | 'assistant' | 'tool',
        content: msg.content,
        toolCallId: msg.toolCallId,
        timestamp: Date.now()
      })
    })
  } catch (e) {
    console.error('Failed to load session:', e)
  }
}

// 创建新会话
async function createSession() {
  try {
    const id = await sessionStore.createSession()
    chatStore.clearMessages()
    connect(id)
  } catch (e) {
    console.error('Failed to create session:', e)
  }
}

// 发送消息
function handleSend(content: string) {
  if (!sessionStore.currentSessionId) return

  // 添加用户消息
  chatStore.addMessage({
    id: Math.random().toString(36).substring(2, 10),
    role: 'user',
    content,
    timestamp: Date.now()
  })

  // 更新会话首条消息
  if (chatStore.messages.length === 1) {
    sessionStore.updateSessionMessageCount(
      sessionStore.currentSessionId,
      1,
      content
    )
  }

  // 发送消息
  sendChat(content)
}

// 停止处理
function handleStop() {
  sendCancel()
}

// 切换模式
function toggleMode() {
  const newMode = sessionStore.permissionMode === 'plan' ? 'default' : 'plan'
  sessionStore.setPermissionMode(newMode)
  sendSetMode(newMode)
}

// 权限确认
function handlePermissionConfirm() {
  if (chatStore.pendingPermission) {
    sendPermissionResponse(chatStore.pendingPermission.requestId, true)
    chatStore.setPendingPermission(null)
  }
}

// 权限拒绝
function handlePermissionDeny() {
  if (chatStore.pendingPermission) {
    sendPermissionResponse(chatStore.pendingPermission.requestId, false)
    chatStore.setPendingPermission(null)
  }
}

// 暴露方法给父组件
defineExpose({
  selectSession,
  createSession
})
</script>

<template>
  <div class="flex flex-col h-full bg-slate-900">
    <!-- 顶部栏 -->
    <AppHeader @toggle-mode="toggleMode" />

    <!-- 消息列表 -->
    <MessageList />

    <!-- 输入框 -->
    <ChatInput
      @send="handleSend"
      @stop="handleStop"
    />

    <!-- 权限确认弹窗 -->
    <PermissionModal
      @confirm="handlePermissionConfirm"
      @deny="handlePermissionDeny"
    />

    <!-- 连接中指示器 -->
    <div
      v-if="isConnecting"
      class="absolute top-0 left-0 right-0 h-1 bg-blue-500 animate-pulse"
    />
  </div>
</template>
