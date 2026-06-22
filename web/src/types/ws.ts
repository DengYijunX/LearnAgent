import type { Message, ToolStatistics } from './chat'
import type { LearningTodo } from './api'

// 服务端 → 客户端 事件
export interface WsSessionReady {
  type: 'session_ready'
  data: {
    session_id: string
    topic: string | null
    permission_mode: 'default' | 'plan'
  }
}

export interface WsTodoUpdate {
  type: 'todo_update'
  data: {
    todos: LearningTodo[]
  }
}

export interface WsCancelled {
  type: 'cancelled'
  data: {
    cancelled: boolean
  }
}

export interface WsThinking {
  type: 'thinking'
  data: {
    turn: number
    max_turns: number
  }
}

export interface WsThought {
  type: 'thought'
  data: {
    turn: number
    has_content: boolean
    content_len: number
  }
}

export interface WsToolStart {
  type: 'tool_start'
  data: {
    name: string
    input: Record<string, unknown>
    turn: number
  }
}

export interface WsToolEnd {
  type: 'tool_end'
  data: {
    name: string
    elapsed: number
    is_error: boolean
    result_summary: string
    result_titles?: string[]
  }
}

export interface WsPermissionRequired {
  type: 'permission_required'
  data: {
    request_id: string
    tool_name: string
    reason: string
    tool_input: Record<string, unknown>
  }
}

export interface WsTopicChange {
  type: 'topic_change'
  data: {
    message: string
    new_topic: string
  }
}

export interface WsCompact {
  type: 'compact'
  data: {
    removed: number
    tokens_before: number
  }
}

export interface WsCompleted {
  type: 'completed'
  data: {
    messages: Message[]
    reason: string
    summary: ToolStatistics
  }
}

export interface WsError {
  type: 'error'
  data: {
    message: string
    code: string
  }
}

// 客户端 → 服务端 消息
export interface WsChat {
  type: 'chat'
  data: {
    content: string
    intent?: string
    topic?: string
  }
}

export interface WsPermissionResponse {
  type: 'permission_response'
  data: {
    request_id: string
    approved: boolean
  }
}

export interface WsCancel {
  type: 'cancel'
  data: Record<string, never>
}

export interface WsSetMode {
  type: 'set_mode'
  data: {
    mode: 'default' | 'plan'
  }
}

export interface WsSetTopic {
  type: 'set_topic'
  data: {
    topic: string
  }
}

// 联合类型
export type WsServerEvent =
  | WsSessionReady
  | WsThinking
  | WsThought
  | WsToolStart
  | WsToolEnd
  | WsPermissionRequired
  | WsTopicChange
  | WsTodoUpdate
  | WsCancelled
  | WsCompact
  | WsCompleted
  | WsError

export type WsClientMessage =
  | WsChat
  | WsPermissionResponse
  | WsCancel
  | WsSetMode
  | WsSetTopic
