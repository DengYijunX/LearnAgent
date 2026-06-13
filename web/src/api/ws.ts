import type { WsServerEvent, WsClientMessage } from '../types/ws'

export interface WebSocketClientOptions {
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  onEvent?: (event: WsServerEvent) => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export class WebSocketClient {
  private ws: WebSocket | null = null
  private sessionId: string | null = null
  private options: Required<WebSocketClientOptions>
  private reconnectAttempts = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private shouldReconnect = true

  constructor(options: WebSocketClientOptions = {}) {
    this.options = {
      onOpen: options.onOpen ?? (() => {}),
      onClose: options.onClose ?? (() => {}),
      onError: options.onError ?? (() => {}),
      onEvent: options.onEvent ?? (() => {}),
      reconnectInterval: options.reconnectInterval ?? 3000,
      maxReconnectAttempts: options.maxReconnectAttempts ?? 5
    }
  }

  connect(sessionId: string): void {
    this.sessionId = sessionId
    this.shouldReconnect = true
    this.reconnectAttempts = 0
    this.doConnect()
  }

  private doConnect(): void {
    if (!this.sessionId) return

    // 使用相对路径，这样无论是通过 Vite 代理还是后端提供静态文件都能工作
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/${this.sessionId}`

    console.log(`Connecting to WebSocket: ${wsUrl}`)
    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      this.options.onOpen()
    }

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason, event.wasClean)
      this.options.onClose()
      this.scheduleReconnect()
    }

    this.ws.onerror = (error) => {
      console.log('WebSocket error:', error)
      this.options.onError(error)
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsServerEvent
        this.options.onEvent(data)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }
  }

  private scheduleReconnect(): void {
    if (!this.shouldReconnect) return
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) return

    this.reconnectAttempts++
    this.reconnectTimer = setTimeout(() => {
      this.doConnect()
    }, this.options.reconnectInterval)
  }

  send(message: WsClientMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  disconnect(): void {
    this.shouldReconnect = false
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  get currentSessionId(): string | null {
    return this.sessionId
  }
}
