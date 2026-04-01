import { useState, useEffect, useRef, useCallback } from 'react'
import type { ChatMessage } from '../types'
import { chatApi } from '../services/api'

const WS_BASE = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws'

export function useChat(conversationId: number | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!conversationId) return

    chatApi.getMessages(conversationId).then((res) => {
      setMessages(res.data)
    })

    const token = localStorage.getItem('access_token')
    const ws = new WebSocket(`${WS_BASE}/chat/${conversationId}/?token=${token}`)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'history') {
        setMessages(data.messages)
      } else if (data.type === 'message') {
        setMessages((prev) => [...prev, data.message])
      }
    }

    return () => {
      ws.close()
      wsRef.current = null
      setConnected(false)
      setMessages([])
    }
  }, [conversationId])

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'message', content }))
    }
  }, [])

  const markRead = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'read' }))
    }
  }, [])

  return { messages, connected, sendMessage, markRead }
}
