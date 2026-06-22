import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SessionSummary } from '../types/api'
import { sessionApi } from '../api/client'

export const useSessionStore = defineStore('session', () => {
  // 状态
  const sessions = ref<SessionSummary[]>([])
  const currentSessionId = ref<string | null>(null)
  const currentTopic = ref<string | null>(null)
  const permissionMode = ref<'default' | 'plan'>('default')
  const isLoading = ref(false)

  // 计算属性
  const currentSession = computed(() =>
    sessions.value.find(s => s.id === currentSessionId.value)
  )

  const hasCurrentSession = computed(() => currentSessionId.value !== null)

  // 方法
  async function loadSessions() {
    isLoading.value = true
    try {
      sessions.value = await sessionApi.getSessions()
    } catch (e) {
      console.error('Failed to load sessions:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function createSession() {
    try {
      const result = await sessionApi.createSession()
      const newSession: SessionSummary = {
        id: result.id,
        messageCount: 0,
        firstMessage: '',
        topic: null,
        intent: "chat",
        createdAt: result.created_at,
        updatedAt: result.created_at
      }
      sessions.value.unshift(newSession)
      currentSessionId.value = result.id
      currentTopic.value = null
      return result.id
    } catch (e) {
      console.error('Failed to create session:', e)
      throw e
    }
  }

  async function deleteSession(id: string) {
    try {
      await sessionApi.deleteSession(id)
      const index = sessions.value.findIndex(s => s.id === id)
      if (index !== -1) {
        sessions.value.splice(index, 1)
      }
      if (currentSessionId.value === id) {
        currentSessionId.value = null
        currentTopic.value = null
      }
    } catch (e) {
      console.error('Failed to delete session:', e)
      throw e
    }
  }

  function setCurrentSession(id: string | null) {
    currentSessionId.value = id
    if (id) {
      const session = sessions.value.find(s => s.id === id)
      if (session) {
        currentTopic.value = session.topic
      }
    } else {
      currentTopic.value = null
    }
  }

  function setCurrentTopic(topic: string | null) {
    currentTopic.value = topic
    if (currentSessionId.value) {
      const session = sessions.value.find(s => s.id === currentSessionId.value)
      if (session) {
        session.topic = topic
      }
    }
  }

  function setPermissionMode(mode: 'default' | 'plan') {
    permissionMode.value = mode
  }

  function updateSessionTopic(id: string, topic: string) {
    const session = sessions.value.find(s => s.id === id)
    if (session) {
      session.topic = topic
      session.updatedAt = new Date().toISOString()
    }
    if (currentSessionId.value === id) {
      currentTopic.value = topic
    }
  }

  function updateSessionMessageCount(id: string, count: number, firstMessage?: string) {
    const session = sessions.value.find(s => s.id === id)
    if (session) {
      session.messageCount = count
      if (firstMessage !== undefined) {
        session.firstMessage = firstMessage
      }
    }
  }

  function reset() {
    sessions.value = []
    currentSessionId.value = null
    currentTopic.value = null
    permissionMode.value = 'default'
    isLoading.value = false
  }

  return {
    // 状态
    sessions,
    currentSessionId,
    currentTopic,
    permissionMode,
    isLoading,
    // 计算属性
    currentSession,
    hasCurrentSession,
    // 方法
    loadSessions,
    createSession,
    deleteSession,
    setCurrentSession,
    setCurrentTopic,
    setPermissionMode,
    updateSessionTopic,
    updateSessionMessageCount,
    reset
  }
})
