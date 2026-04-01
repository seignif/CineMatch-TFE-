import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Send } from 'lucide-react'
import { useChat } from '../hooks/useChat'
import { chatApi } from '../services/api'
import { useAuthStore } from '../store/authStore'
import type { Conversation } from '../types'

function formatTime(dateStr: string) {
  return new Date(dateStr).toLocaleTimeString('fr-BE', { hour: '2-digit', minute: '2-digit' })
}

export default function ConversationView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const convId = id ? parseInt(id) : null
  const { messages, connected, sendMessage, markRead } = useChat(convId)
  const [input, setInput] = useState('')
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!convId) return
    chatApi.getConversations().then(res => {
      const conv = res.data.find((c: Conversation) => c.id === convId)
      if (conv) setConversation(conv)
    })
  }, [convId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (connected) markRead()
  }, [connected, markRead])

  const handleSend = () => {
    const content = input.trim()
    if (!content || !connected) return
    sendMessage(content)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const other = conversation?.other_user

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto">
      {/* Header */}
      <div className="glass border-b border-white/5 px-4 py-3 flex items-center gap-3 shrink-0">
        <button onClick={() => navigate('/chat')}
          className="p-2 rounded-lg hover:bg-white/5 transition-colors">
          <ArrowLeft size={18} />
        </button>

        {other && (
          <>
            <div className="w-9 h-9 rounded-full overflow-hidden border"
              style={{ borderColor: 'var(--accent-red)' }}>
              {other.profile_picture ? (
                <img src={other.profile_picture} alt={other.first_name} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-sm font-bold"
                  style={{ background: 'var(--bg-card)', color: 'var(--accent-red)' }}>
                  {other.first_name[0].toUpperCase()}
                </div>
              )}
            </div>
            <div className="flex-1">
              <p className="font-medium text-white text-sm">{other.first_name}</p>
              {other.city && <p className="text-xs text-[var(--text-muted)]">{other.city}</p>}
            </div>
          </>
        )}

        {/* Indicateur connexion */}
        <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
          {connected ? 'Connecté' : 'Reconnexion...'}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-[var(--text-muted)] text-sm py-8">
            Démarrez la conversation !
          </div>
        )}
        {messages.map(msg => {
          const isMe = msg.sender_id === user?.id
          return (
            <div key={msg.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[75%] rounded-2xl px-4 py-2 ${isMe ? 'rounded-br-sm' : 'rounded-bl-sm'}`}
                style={{
                  background: isMe ? 'var(--accent-red)' : 'rgba(255,255,255,0.08)',
                  color: isMe ? 'white' : 'var(--text-primary)',
                }}>
                {!isMe && (
                  <p className="text-xs font-medium mb-0.5" style={{ color: 'var(--accent-gold)' }}>
                    {msg.sender_name}
                  </p>
                )}
                <p className="text-sm leading-relaxed">{msg.content}</p>
                <p className={`text-xs mt-1 ${isMe ? 'text-white/60' : 'text-[var(--text-muted)]'}`}>
                  {formatTime(msg.created_at)}
                </p>
              </div>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="glass border-t border-white/5 px-4 py-3 flex items-center gap-3 shrink-0">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={connected ? 'Votre message...' : 'Connexion en cours...'}
          disabled={!connected}
          className="flex-1 input-field text-sm disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || !connected}
          className="w-10 h-10 rounded-xl flex items-center justify-center transition-colors disabled:opacity-40"
          style={{ background: 'var(--accent-red)' }}
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}
