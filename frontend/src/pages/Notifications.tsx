import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, Check } from 'lucide-react'
import type { SocialNotification } from '../types'
import { socialApi } from '../services/api'
import { formatDistanceToNow } from '../utils/dateUtils'
import { mediaUrl } from '../utils/media'

const TYPE_ICON: Record<SocialNotification['type'], string> = {
  like_post: '❤️',
  comment_post: '💬',
  new_match: '🎉',
  group_invitation: '👥',
  outing_confirmed: '🍿',
}

export default function Notifications() {
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState<SocialNotification[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await socialApi.getNotifications()
        setNotifications(res.data.results ?? res.data)
      } catch {
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleMarkAllRead = async () => {
    try {
      await socialApi.markAllRead()
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
    } catch {}
  }

  const handleClick = async (notif: SocialNotification) => {
    if (!notif.is_read) {
      try {
        await socialApi.markOneRead(notif.id)
        setNotifications(prev =>
          prev.map(n => n.id === notif.id ? { ...n, is_read: true } : n)
        )
      } catch {}
    }

    if (notif.post_preview) {
      navigate('/entracte')
    } else if (notif.type === 'new_match') {
      navigate('/matches')
    } else if (notif.type === 'group_invitation') {
      navigate('/groups')
    } else if (notif.type === 'outing_confirmed') {
      navigate('/outings')
    }
  }

  const unreadCount = notifications.filter(n => !n.is_read).length

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-display font-bold text-white tracking-wider uppercase">
            Notifications
          </h1>
          {unreadCount > 0 && (
            <p className="text-[var(--text-muted)] text-sm mt-0.5">
              {unreadCount} non lue{unreadCount > 1 ? 's' : ''}
            </p>
          )}
        </div>
        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllRead}
            className="flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-white transition-colors"
          >
            <Check size={15} />
            Tout marquer comme lu
          </button>
        )}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-[var(--bg-card)] rounded-xl p-4 animate-pulse flex gap-3">
              <div className="w-10 h-10 rounded-full bg-white/10 flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-3 bg-white/10 rounded w-3/4" />
                <div className="h-2 bg-white/10 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : notifications.length === 0 ? (
        <div className="text-center py-16">
          <Bell size={40} className="mx-auto text-[var(--text-muted)] mb-3" />
          <p className="text-white font-semibold">Aucune notification</p>
          <p className="text-[var(--text-muted)] text-sm mt-1">
            Vos interactions apparaîtront ici
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map(notif => (
            <div
              key={notif.id}
              onClick={() => handleClick(notif)}
              className={`flex items-start gap-3 p-4 rounded-xl cursor-pointer transition-colors ${
                notif.is_read
                  ? 'bg-[var(--bg-card)] hover:bg-white/5'
                  : 'bg-[var(--accent-red)]/10 hover:bg-[var(--accent-red)]/15 border border-[var(--accent-red)]/20'
              }`}
            >
              {/* Avatar ou icône */}
              <div className="relative flex-shrink-0">
                {notif.triggered_by_picture ? (
                  <img
                    src={mediaUrl(notif.triggered_by_picture!)}
                    alt={notif.triggered_by_name ?? ''}
                    className="w-10 h-10 rounded-full object-cover bg-white/10"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center text-lg">
                    {TYPE_ICON[notif.type]}
                  </div>
                )}
                {notif.triggered_by_picture && (
                  <span className="absolute -bottom-0.5 -right-0.5 text-sm">
                    {TYPE_ICON[notif.type]}
                  </span>
                )}
              </div>

              {/* Contenu */}
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm leading-snug">{notif.message}</p>
                {notif.post_preview && (
                  <p className="text-[var(--text-muted)] text-xs mt-1 truncate">
                    "{notif.post_preview.content}"
                  </p>
                )}
                <p className="text-[var(--text-muted)] text-xs mt-1">
                  {formatDistanceToNow(notif.created_at)}
                </p>
              </div>

              {/* Point non lu */}
              {!notif.is_read && (
                <div className="w-2 h-2 rounded-full bg-[var(--accent-red)] flex-shrink-0 mt-1.5" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
