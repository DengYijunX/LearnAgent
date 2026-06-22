import type {
  SessionSummary,
  SessionDetail,
  SessionSummaryResponse,
  SessionDetailResponse,
  SessionsResponse,
  CreateSessionResponse,
  DeleteSessionResponse,
  ChatResponse,
  ToolsResponse,
  ConfigInfo,
  ChatRequest,
  TodosResponse,
  MemoriesResponse,
  ProcessesResponse,
  StopProcessResponse
} from '../types/api'

const API_BASE = '/api'

function normalizeSession(summary: SessionSummaryResponse): SessionSummary {
  return {
    id: summary.id,
    messageCount: summary.message_count,
    firstMessage: summary.first_message,
    topic: summary.topic,
    intent: summary.intent || 'chat',
    createdAt: summary.created_at,
    updatedAt: summary.updated_at
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  })

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

// 会话管理 API
export const sessionApi = {
  // 获取所有会话
  async getSessions(): Promise<SessionSummary[]> {
    const res = await request<SessionsResponse>('/sessions')
    return res.sessions.map(normalizeSession)
  },

  // 创建新会话
  async createSession(): Promise<CreateSessionResponse> {
    return request<CreateSessionResponse>('/sessions', {
      method: 'POST'
    })
  },

  // 获取会话详情
  async getSession(id: string): Promise<SessionDetail> {
    const detail = await request<SessionDetailResponse>(`/sessions/${id}`)
    return {
      ...normalizeSession(detail),
      permissionMode: detail.permission_mode,
      messages: detail.messages
    }
  },

  // 删除会话
  async deleteSession(id: string): Promise<DeleteSessionResponse> {
    return request<DeleteSessionResponse>(`/sessions/${id}`, {
      method: 'DELETE'
    })
  },

  // 重命名会话
  async renameSession(id: string, topic: string): Promise<{ id: string; topic: string | null }> {
    return request(`/sessions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ topic })
    })
  }
}

// 聊天 API
export const chatApi = {
  // 发送消息
  async sendMessage(req: ChatRequest): Promise<ChatResponse> {
    return request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(req)
    })
  }
}

// 工具 API
export const toolApi = {
  // 获取工具列表
  async getTools(): Promise<ToolsResponse> {
    return request<ToolsResponse>('/tools')
  }
}

// 配置 API
export const configApi = {
  // 获取配置
  async getConfig(): Promise<ConfigInfo> {
    return request<ConfigInfo>('/config')
  }
}

export const contextApi = {
  async getTodos(sessionId: string): Promise<TodosResponse> {
    return request<TodosResponse>(`/sessions/${sessionId}/todos`)
  },

  async getMemories(limit = 3): Promise<MemoriesResponse> {
    return request<MemoriesResponse>(`/memories?type=learning&limit=${limit}`)
  },

  async getProcesses(sessionId: string): Promise<ProcessesResponse> {
    return request<ProcessesResponse>(`/processes?session_id=${encodeURIComponent(sessionId)}`)
  },

  async stopProcess(pid: number, sessionId: string): Promise<StopProcessResponse> {
    return request<StopProcessResponse>(`/processes/${pid}/stop?session_id=${encodeURIComponent(sessionId)}`, {
      method: 'POST'
    })
  },

  async getConfig(): Promise<ConfigInfo> {
    return request<ConfigInfo>('/config')
  },

  async getTools(): Promise<ToolsResponse> {
    return request<ToolsResponse>('/tools')
  }
}
