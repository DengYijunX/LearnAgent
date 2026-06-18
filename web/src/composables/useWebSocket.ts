import { ref, onUnmounted } from 'vue'
import { WebSocketClient } from '../api/ws'
import { useChatStore } from '../stores/chat'
import { useSessionStore } from '../stores/session'
import type { WsServerEvent } from '../types/ws'
import type { Message } from '../types/chat'

export function useWebSocket() {
  const chatStore = useChatStore()
  const sessionStore = useSessionStore()

  const client = ref<WebSocketClient | null>(null)
  const isConnecting = ref(false)

  function generateId(): string {
    return Math.random().toString(36).substring(2, 10)
  }

  function handleEvent(event: WsServerEvent) {
    switch (event.type) {
      case 'session_ready':
        sessionStore.setCurrentSession(event.data.session_id)
        if (event.data.topic) {
          sessionStore.setCurrentTopic(event.data.topic)
        }
        break

      case 'thinking':
        chatStore.setThinking(event.data.turn, event.data.max_turns)
        break

      case 'thought':
        // 创建或更新助手消息
        const existingAssistant = chatStore.messages.find(
          m => m.role === 'assistant' && !m.toolCallId
        )
        if (existingAssistant) {
          chatStore.updateMessage(existingAssistant.id, {
            content: event.data.has_content ? existingAssistant.content : '思考中...'
          })
        } else if (event.data.has_content) {
          chatStore.addMessage({
            id: generateId(),
            role: 'assistant',
            content: '',
            timestamp: Date.now()
          })
        }
        break

      case 'tool_start': {
        const toolId = generateId()
        const toolDescription = getToolDescription(event.data.name, event.data.input)
        chatStore.addToolCall({
          id: toolId,
          name: event.data.name,
          input: event.data.input,
          status: 'running',
          description: toolDescription
        })
        // 添加一个占位消息用于关联
        chatStore.addMessage({
          id: generateId(),
          role: 'tool',
          content: toolDescription,
          toolCallId: toolId,
          timestamp: Date.now()
        })
        break
      }

      case 'tool_end': {
        const toolCalls = Array.from(chatStore.activeToolCalls.values())
        const lastTool = toolCalls[toolCalls.length - 1]
        if (lastTool) {
          chatStore.updateToolCall(lastTool.id, {
            status: event.data.is_error ? 'error' : 'done',
            elapsed: event.data.elapsed,
            resultSummary: event.data.result_summary,
            resultTitles: event.data.result_titles
          })
        }
        break
      }

      case 'permission_required':
        chatStore.setPendingPermission({
          requestId: event.data.request_id,
          toolName: event.data.tool_name,
          reason: event.data.reason,
          toolInput: event.data.tool_input
        })
        break

      case 'topic_change':
        sessionStore.setCurrentTopic(event.data.new_topic)
        break

      case 'completed':
        chatStore.setProcessing(false)
        chatStore.setCompleted(event.data.summary)

        // 检查 thought 事件是否已经创建了最后一个 assistant 消息占位
        // 如果有内容且最后一条消息已经是 assistant（由 thought 事件创建），
        // 则更新它而不是新建，避免重复显示同一句话
        if (event.data.messages && event.data.messages.length > 0) {
          const lastAssistantFromLoop = [...event.data.messages]
            .reverse()
            .find((m: any) => m.role === 'assistant' && m.content)

          if (lastAssistantFromLoop) {
            const existingPlaceholder = [...chatStore.messages]
              .reverse()
              .find((m: Message) => m.role === 'assistant' && !m.content)

            if (existingPlaceholder) {
              chatStore.updateMessage(existingPlaceholder.id, {
                content: lastAssistantFromLoop.content
              })
            } else {
              chatStore.addMessage({
                id: generateId(),
                role: 'assistant',
                content: lastAssistantFromLoop.content,
                timestamp: Date.now()
              })
            }
          }
        }

        // 更新会话消息数
        if (sessionStore.currentSessionId) {
          sessionStore.updateSessionMessageCount(
            sessionStore.currentSessionId,
            chatStore.messages.length
          )
        }
        break

      case 'error':
        chatStore.setProcessing(false)
        console.error('WebSocket error:', event.data.message)
        break
    }
  }

  function getToolDescription(name: string, input: Record<string, unknown>): string {
    switch (name) {
      case 'search_web':
        return `搜索「${input.query || ''}」...`
      case 'read_url':
        return `读取网页: ${input.url || ''}`
      case 'file_write':
        return `写入文件: ${input.path || ''}`
      case 'file_read':
        return `读取文件: ${input.path || ''}`
      case 'run_code':
        return `运行代码...`
      case 'execute_command':
        return `执行命令: ${input.command || ''}`
      default:
        return `${name}...`
    }
  }

  function connect(sessionId: string) {
    if (client.value) {
      client.value.disconnect()
    }

    isConnecting.value = true
    chatStore.reset()

    console.log(`Connecting to WebSocket with sessionId: ${sessionId}`)

    client.value = new WebSocketClient({
      onOpen: () => {
        console.log('WebSocket connected')
        isConnecting.value = false
        chatStore.setWsConnected(true)
      },
      onClose: () => {
        console.log('WebSocket disconnected')
        isConnecting.value = false
        chatStore.setWsConnected(false)
      },
      onError: (error) => {
        console.log('WebSocket error:', error)
        isConnecting.value = false
        console.error('WebSocket error:', error)
      },
      onEvent: (event) => {
        console.log('Received WebSocket event:', event.type, event.data)
        handleEvent(event)
      }
    })

    client.value.connect(sessionId)
  }

  function disconnect() {
    if (client.value) {
      client.value.disconnect()
      client.value = null
    }
    chatStore.setWsConnected(false)
  }

  function sendChat(content: string, intent?: string, topic?: string) {
    if (client.value) {
      client.value.send({
        type: 'chat',
        data: { content, intent, topic }
      })
    }
  }

  function sendPermissionResponse(requestId: string, approved: boolean) {
    if (client.value) {
      client.value.send({
        type: 'permission_response',
        data: { request_id: requestId, approved }
      })
    }
  }

  function sendCancel() {
    if (client.value) {
      client.value.send({ type: 'cancel', data: {} })
    }
  }

  function sendSetMode(mode: 'default' | 'plan') {
    if (client.value) {
      client.value.send({ type: 'set_mode', data: { mode } })
    }
  }

  function sendCommand(command: string) {
    if (client.value) {
      client.value.send({ type: 'command', data: { command } })
    }
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    client,
    isConnecting,
    connect,
    disconnect,
    sendChat,
    sendPermissionResponse,
    sendCancel,
    sendSetMode,
    sendCommand
  }
}
