// 消息类型
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  toolCallId?: string
  isError?: boolean
  timestamp: number
}

// 工具调用状态
export interface ToolCallState {
  id: string
  name: string
  input: Record<string, unknown>
  status: 'running' | 'done' | 'error'
  description: string
  elapsed?: number
  resultSummary?: string
  resultTitles?: string[]
}

// 权限请求
export interface PermissionRequest {
  requestId: string
  toolName: string
  reason: string
  toolInput: Record<string, unknown>
}

// 工具统计
export interface ToolStatistics {
  turns: number
  tools: Record<string, number>
}
