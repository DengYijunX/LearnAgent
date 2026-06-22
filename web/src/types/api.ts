import type { Message } from './chat'

// 会话相关类型
export interface SessionSummary {
  id: string
  messageCount: number
  firstMessage: string
  topic: string | null
  intent: string
  createdAt: string
  updatedAt: string
}

export interface SessionDetail extends SessionSummary {
  permissionMode: 'default' | 'plan'
  messages: Message[]
}

export interface SessionSummaryResponse {
  id: string
  message_count: number
  first_message: string
  topic: string | null
  intent?: string
  created_at: string
  updated_at: string
}

export interface SessionDetailResponse extends SessionSummaryResponse {
  intent: string
  permission_mode: 'default' | 'plan'
  messages: Message[]
}

export interface LearningTodo {
  content: string
  active_form: string | null
  status: 'pending' | 'in_progress' | 'completed'
}

export interface LearningMemory {
  name: string
  description: string
  type: string
  body: string
}

export interface RuntimeProcess {
  pid: number
  command: string
  port?: number | null
  elapsed: number
  session_id?: string
}

// 聊天相关类型
export interface ChatRequest {
  content: string
  session_id?: string
  intent?: string
  topic?: string
}

export interface ChatResponse {
  session_id: string
  message: string
}

// 工具相关类型
export interface ToolInfo {
  name: string
  description: string
  read_only: boolean
}

// 配置相关类型
export interface ConfigInfo {
  model_mode: string
  base_url: string
  storage_dir: string
  api_key_configured: boolean
}

// API 响应类型
export interface SessionsResponse {
  sessions: SessionSummaryResponse[]
}

export interface CreateSessionResponse {
  id: string
  created_at: string
}

export interface DeleteSessionResponse {
  deleted: boolean
}

export interface ToolsResponse {
  tools: ToolInfo[]
}

export interface TodosResponse {
  todos: LearningTodo[]
}

export interface MemoriesResponse {
  memories: LearningMemory[]
}

export interface ProcessesResponse {
  processes: RuntimeProcess[]
}

export interface StopProcessResponse {
  stopped: boolean
  pid: number
}
