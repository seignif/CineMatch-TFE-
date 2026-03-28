import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageCircle } from 'lucide-react'
import { chatApi } from '../services/api'
import type { Conversation } from '../types'

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "à l'instant"
  if (mins < 60) return `il y a ${mins} min`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `il y a ${hrs}h`
  return `il y a ${Math.floor(hrs / 24)}j`
}

export default function Chat() {
  const navigate = useNavigate()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    chatApi.getConversations()
      .then(res => setConversations(res.data))
      .catch(() => setConversations([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-12 h-12 border-2 border-[var(--accent-red)] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen max-w-2xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="font-display text-5xl tracking-wider text-white">
          MESSAGES
        </h1>
        <p className="text-[var(--text-muted)] mt-1">
          {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
        </p>
      </div>

      {conversations.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <MessageCircle size={48} className="mb-4 text-[var(--text-muted)]" />
          <h2 className="text-xl font-semibold text-white mb-2">Aucune conversation</h2>
          <p className="text-[var(--text-muted)] text-sm mb-6">
            Vos conversations avec vos matchs apparaîtront ici.
          </p>
          <button onClick={() => navigate('/matches')} className="btn-primary">
            Voir mes matchs
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {conversations.map(conv => {
            const other = conv.other_user
            return (
              <button
                key={conv.id}
                onClick={() => navigate(`/chat/${conv.id}`)}
                className="w-full glass rounded-xl p-4 flex items-center gap-4 hover:bg-white/5 transition-colors text-left"
              >
                {/* Avatar */}
                <div className="relative shrink-0">
                  <div className="w-12 h-12 rounded-full overflow-hidden border-2"
                    style={{ borderColor: 'var(--accent-red)' }}>
                    {other.profile_picture ? (
                      <img src={other.profile_picture} alt={other.first_name}
                        className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-xl font-bold"
                        style={{ background: 'var(--bg-card)', color: 'var(--accent-red)' }}>
                        {other.first_name[0].toUpperCase()}
                      </div>
                    )}
                  </div>
                  {conv.unread_count > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full text-xs flex items-center justify-center font-bold"
                      style={{ background: 'var(--accent-red)' }}>
                      {conv.unread_count > 9 ? '9+' : conv.unread_count}
                    </span>
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className={`font-medium ${conv.unread_count > 0 ? 'text-white' : 'text-[var(--text-primary)]'}`}>
                      {other.first_name}
                    </span>
                    {conv.last_message && (
                      <span className="text-xs text-[var(--text-muted)] shrink-0">
                        {timeAgo(conv.last_message.created_at)}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-[var(--text-muted)] truncate mt-0.5">
                    {conv.last_message
                      ? `${conv.last_message.sender_name}: ${conv.last_message.content}`
                      : 'Démarrez la conversation !'}
                  </div>
                </div>

                {/* Score */}
                <span className="text-xs shrink-0" style={{ color: 'var(--accent-gold)' }}>
                  {conv.match_score}%
                </span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
