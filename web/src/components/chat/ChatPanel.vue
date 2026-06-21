<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import AppHeader from '../layout/AppHeader.vue'
import MessageList from './MessageList.vue'
import ChatInput from './ChatInput.vue'
import PermissionModal from '../common/PermissionModal.vue'
import LearningContextPanel from '../context/LearningContextPanel.vue'
import { useChatStore } from '../../stores/chat'
import { useSessionStore } from '../../stores/session'
import { useContextStore } from '../../stores/context'
import { useWebSocket } from '../../composables/useWebSocket'
import { useContextPanel } from '../../composables/useContextPanel'

const chatStore = useChatStore()
const sessionStore = useSessionStore()
const contextStore = useContextStore()
const { isOpen, isPinned, isOverlay, toggle, close, togglePinned } = useContextPanel()
const chatInputRef = ref<InstanceType<typeof ChatInput> | null>(null)
const {
  connect,
  disconnect,
  sendChat,
  sendPermissionResponse,
  sendCancel,
  sendSetMode,
  sendSetTopic,
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
    contextStore.clear()
    if (newId) {
      connect(newId)
      await contextStore.load(newId)
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
    await contextStore.load(id)
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

function handlePromptSelect(prompt: string) {
  chatInputRef.value?.setDraft(prompt)
}

// 切换模式
function toggleMode() {
  const newMode = sessionStore.permissionMode === 'plan' ? 'default' : 'plan'
  sessionStore.setPermissionMode(newMode)
  sendSetMode(newMode)
}

function setTopic(topic: string) {
  sessionStore.setCurrentTopic(topic)
  sendSetTopic(topic)
}

function refreshContext() {
  if (sessionStore.currentSessionId) contextStore.load(sessionStore.currentSessionId)
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
  <div class="relative flex h-full min-w-0 bg-white/20">
    <section class="relative flex min-w-0 flex-1 flex-col">
      <!-- 顶部栏 -->
      <AppHeader :context-open="isOpen" @toggle-mode="toggleMode" @toggle-context="toggle" />

      <!-- 消息列表 -->
      <MessageList @select-prompt="handlePromptSelect" />

      <!-- 输入框 -->
      <ChatInput
        ref="chatInputRef"
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
        class="pointer-events-none absolute left-1/2 top-[76px] z-30 -translate-x-1/2 rounded-full border border-blue-100 bg-white/90 px-3 py-1.5 text-[11px] font-medium text-blue-700 shadow-lg backdrop-blur-xl"
        role="status"
      >
        正在连接会话…
      </div>
    </section>

    <LearningContextPanel
      :open="isOpen"
      :pinned="isPinned"
      :overlay="isOverlay"
      @close="close"
      @toggle-pin="togglePinned"
      @refresh="refreshContext"
      @toggle-mode="toggleMode"
      @set-topic="setTopic"
    />
  </div>
</template>
