const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws'

type MessageHandler = (data: Record<string, unknown>) => void

export class ChatWebSocket {
  private socket: WebSocket | null = null
  private conversationId: number
  private onMessage: MessageHandler
  private reconnectAttempts = 0
  private readonly maxReconnects = 5

  constructor(conversationId: number, onMessage: MessageHandler) {
    this.conversationId = conversationId
    this.onMessage = onMessage
  }

  connect() {
    const token = localStorage.getItem('access_token')
    const url = `${WS_BASE_URL}/chat/${this.conversationId}/?token=${token}`

    this.socket = new WebSocket(url)

    this.socket.onopen = () => {
      console.log(`[WS] Connecté à la conversation ${this.conversationId}`)
      this.reconnectAttempts = 0
    }

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.onMessage(data)
      } catch (e) {
        console.error('[WS] Erreur parsing message:', e)
      }
    }

    this.socket.onclose = (event) => {
      console.log(`[WS] Déconnecté (code: ${event.code})`)
      if (!event.wasClean && this.reconnectAttempts < this.maxReconnects) {
        const delay = Math.pow(2, this.reconnectAttempts) * 1000
        setTimeout(() => {
          this.reconnectAttempts++
          this.connect()
        }, delay)
      }
    }

    this.socket.onerror = (error) => {
      console.error('[WS] Erreur:', error)
    }
  }

  sendMessage(content: string) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ message: content }))
    }
  }

  disconnect() {
    this.socket?.close()
  }
}
