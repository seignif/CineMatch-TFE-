import { useState, useEffect, useRef, useCallback } from 'react'
import type { GroupMessage } from '../types'
import { groupsApi } from '../services/api'

const WS_BASE = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws'

export function useGroupChat(groupId: number | null) {
  const [messages, setMessages] = useState<GroupMessage[]>([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!groupId) return

    groupsApi.getMessages(groupId).then((res) => setMessages(res.data.results ?? res.data)).catch(() => {})

    const token = localStorage.getItem('access_token')
    const ws = new WebSocket(`${WS_BASE}/group/${groupId}/?token=${token}`)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'history') setMessages(data.messages)
      else if (data.type === 'message') setMessages((prev) => [...prev, data.message])
    }

    return () => {
      ws.close()
      wsRef.current = null
      setConnected(false)
      setMessages([])
    }
  }, [groupId])

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'message', content }))
    }
  }, [])

  return { messages, connected, sendMessage }
}
