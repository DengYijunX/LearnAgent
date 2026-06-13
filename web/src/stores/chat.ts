import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Message, ToolCallState, PermissionRequest, ToolStatistics } from '../types/chat'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const messages = ref<Message[]>([])
  const isProcessing = ref(false)
  const activeToolCalls = ref<Map<string, ToolCallState>>(new Map())
  const pendingPermission = ref<PermissionRequest | null>(null)
  const wsConnected = ref(false)
  const currentTurn = ref(0)
  const maxTurns = ref(8)
  const toolStatistics = ref<ToolStatistics | null>(null)

  // 计算属性
  const hasPendingPermission = computed(() => pendingPermission.value !== null)

  // 方法
  function addMessage(message: Message) {
    messages.value.push(message)
  }

  function updateMessage(id: string, updates: Partial<Message>) {
    const index = messages.value.findIndex(m => m.id === id)
    if (index !== -1) {
      messages.value[index] = { ...messages.value[index], ...updates }
    }
  }

  function addToolCall(toolCall: ToolCallState) {
    activeToolCalls.value.set(toolCall.id, toolCall)
  }

  function updateToolCall(id: string, updates: Partial<ToolCallState>) {
    const toolCall = activeToolCalls.value.get(id)
    if (toolCall) {
      activeToolCalls.value.set(id, { ...toolCall, ...updates })
    }
  }

  function removeToolCall(id: string) {
    activeToolCalls.value.delete(id)
  }

  function setProcessing(processing: boolean) {
    isProcessing.value = processing
  }

  function setPendingPermission(permission: PermissionRequest | null) {
    pendingPermission.value = permission
  }

  function setWsConnected(connected: boolean) {
    wsConnected.value = connected
  }

  function setThinking(turn: number, maxTurnsVal: number) {
    currentTurn.value = turn
    maxTurns.value = maxTurnsVal
    isProcessing.value = true
  }

  function setCompleted(summary: ToolStatistics) {
    isProcessing.value = false
    toolStatistics.value = summary
  }

  function clearMessages() {
    messages.value = []
    activeToolCalls.value.clear()
    toolStatistics.value = null
  }

  function reset() {
    messages.value = []
    isProcessing.value = false
    activeToolCalls.value.clear()
    pendingPermission.value = null
    wsConnected.value = false
    currentTurn.value = 0
    maxTurns.value = 8
    toolStatistics.value = null
  }

  return {
    // 状态
    messages,
    isProcessing,
    activeToolCalls,
    pendingPermission,
    wsConnected,
    currentTurn,
    maxTurns,
    toolStatistics,
    // 计算属性
    hasPendingPermission,
    // 方法
    addMessage,
    updateMessage,
    addToolCall,
    updateToolCall,
    removeToolCall,
    setProcessing,
    setPendingPermission,
    setWsConnected,
    setThinking,
    setCompleted,
    clearMessages,
    reset
  }
})
