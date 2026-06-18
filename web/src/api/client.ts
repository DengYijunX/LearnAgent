import type {
  SessionSummary,
  SessionDetail,
  SessionsResponse,
  CreateSessionResponse,
  DeleteSessionResponse,
  ChatResponse,
  ToolsResponse,
  ConfigInfo,
  ChatRequest
} from '../types/api'

const API_BASE = '/api'

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
    return res.sessions
  },

  // 创建新会话
  async createSession(): Promise<CreateSessionResponse> {
    return request<CreateSessionResponse>('/sessions', {
      method: 'POST'
    })
  },

  // 获取会话详情
  async getSession(id: string): Promise<SessionDetail> {
    return request<SessionDetail>(`/sessions/${id}`)
  },

  // 删除会话
  async deleteSession(id: string): Promise<DeleteSessionResponse> {
    return request<DeleteSessionResponse>(`/sessions/${id}`, {
      method: 'DELETE'
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
