import { defineStore } from 'pinia'
import { ref } from 'vue'
import { contextApi } from '../api/client'
import type {
  ConfigInfo,
  LearningMemory,
  LearningTodo,
  RuntimeProcess,
  ToolInfo
} from '../types/api'

type ContextSection = 'todos' | 'memories' | 'processes' | 'config' | 'tools'

export const useContextStore = defineStore('context', () => {
  const todos = ref<LearningTodo[]>([])
  const memories = ref<LearningMemory[]>([])
  const processes = ref<RuntimeProcess[]>([])
  const config = ref<ConfigInfo | null>(null)
  const tools = ref<ToolInfo[]>([])
  const isLoading = ref(false)
  const errors = ref<Partial<Record<ContextSection, string>>>({})
  const lastRefreshedAt = ref<number | null>(null)
  let requestToken = 0

  function errorMessage(error: unknown): string {
    return error instanceof Error ? error.message : '加载失败，请稍后重试。'
  }

  function setTodos(snapshot: LearningTodo[]) {
    todos.value = snapshot.map(item => ({ ...item }))
    delete errors.value.todos
  }

  function clear() {
    requestToken++
    todos.value = []
    memories.value = []
    processes.value = []
    config.value = null
    tools.value = []
    errors.value = {}
    lastRefreshedAt.value = null
    isLoading.value = false
  }

  async function load(sessionId: string) {
    const token = ++requestToken
    isLoading.value = true
    errors.value = {}
    const sections: Array<[ContextSection, Promise<unknown>]> = [
      ['todos', contextApi.getTodos(sessionId)],
      ['memories', contextApi.getMemories(3)],
      ['processes', contextApi.getProcesses(sessionId)],
      ['config', contextApi.getConfig()],
      ['tools', contextApi.getTools()]
    ]
    const results = await Promise.allSettled(sections.map(([, request]) => request))
    if (token !== requestToken) return

    results.forEach((result, index) => {
      const section = sections[index][0]
      if (result.status === 'rejected') {
        errors.value[section] = errorMessage(result.reason)
        return
      }
      const value = result.value as any
      if (section === 'todos') todos.value = value.todos
      if (section === 'memories') memories.value = value.memories
      if (section === 'processes') processes.value = value.processes
      if (section === 'config') config.value = value
      if (section === 'tools') tools.value = value.tools
    })
    lastRefreshedAt.value = Date.now()
    isLoading.value = false
  }

  async function refreshProcesses(sessionId: string) {
    try {
      const result = await contextApi.getProcesses(sessionId)
      processes.value = result.processes
      delete errors.value.processes
    } catch (error) {
      errors.value.processes = errorMessage(error)
      throw error
    }
  }

  async function stopProcess(pid: number, sessionId: string) {
    const result = await contextApi.stopProcess(pid, sessionId)
    if (result.stopped) await refreshProcesses(sessionId)
    return result.stopped
  }

  return {
    todos,
    memories,
    processes,
    config,
    tools,
    isLoading,
    errors,
    lastRefreshedAt,
    setTodos,
    load,
    clear,
    refreshProcesses,
    stopProcess
  }
})
