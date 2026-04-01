import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Heart, MessageCircle, MapPin } from 'lucide-react'
import { matchingApi, chatApi } from '../services/api'
import type { Match } from '../types'

const MOOD_LABELS: Record<string, string> = {
  rire: 'Envie de rire',
  reflechir: 'Besoin de réfléchir',
  emu: "Envie d'être ému",
  adrenaline: "Besoin d'adrénaline",
}

export default function Matches() {
  const navigate = useNavigate()
  const [matches, setMatches] = useState<Match[]>([])
  const [loading, setLoading] = useState(true)
  const [openingChat, setOpeningChat] = useState<number | null>(null)

  useEffect(() => {
    matchingApi.getMatches()
      .then(res => setMatches(res.data))
      .catch(() => setMatches([]))
      .finally(() => setLoading(false))
  }, [])

  const handleOpenChat = async (match: Match) => {
    setOpeningChat(match.id)
    try {
      const res = await chatApi.createConversation(match.id)
      navigate(`/chat/${res.data.id}`)
    } catch {
      navigate('/chat')
    } finally {
      setOpeningChat(null)
    }
  }

  const calcAge = (dob?: string | null) => {
    if (!dob) return null
    return Math.floor((Date.now() - new Date(dob).getTime()) / (365.25 * 24 * 3600 * 1000))
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-12 h-12 border-2 border-[var(--accent-red)] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen max-w-3xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="font-display text-5xl tracking-wider text-white">
          MES <span style={{ color: 'var(--accent-red)' }}>MATCHS</span>
        </h1>
        <p className="text-[var(--text-muted)] mt-1">
          {matches.length} match{matches.length !== 1 ? 's' : ''} actif{matches.length !== 1 ? 's' : ''}
        </p>
      </div>

      {matches.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <Heart size={48} className="mb-4" style={{ color: 'var(--accent-red)' }} />
          <h2 className="text-xl font-semibold text-white mb-2">Pas encore de matchs</h2>
          <p className="text-[var(--text-muted)] text-sm mb-6">
            Allez swiper des profils pour trouver des matchs !
          </p>
          <button onClick={() => navigate('/matching')} className="btn-primary">
            Commencer à swiper
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {matches.map(match => {
            const other = match.other_user
            const reasons = match.ai_generated_reasons?.length
              ? match.ai_generated_reasons
              : match.raisons_compatibilite

            return (
              <div key={match.id} className="glass rounded-2xl p-5 flex items-start gap-4">
                {/* Avatar */}
                <div className="w-16 h-16 rounded-full overflow-hidden shrink-0 border-2"
                  style={{ borderColor: 'var(--accent-red)' }}>
                  {other.profile?.profile_picture ? (
                    <img src={other.profile.profile_picture} alt={other.first_name}
                      className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-2xl font-bold"
                      style={{ background: 'var(--bg-card)', color: 'var(--accent-red)' }}>
                      {other.first_name?.[0]?.toUpperCase() ?? '?'}
                    </div>
                  )}
                </div>

                {/* Infos */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <h3 className="text-lg font-semibold text-white">
                      {other.first_name}
                      {calcAge(null) !== null ? '' : ''}
                    </h3>
                    <span className="text-sm font-bold px-3 py-1 rounded-full shrink-0"
                      style={{ background: 'rgba(255,215,0,0.15)', color: 'var(--accent-gold)', border: '1px solid rgba(255,215,0,0.3)' }}>
                      {match.score_compatibilite}% compat.
                    </span>
                  </div>

                  {other.city && (
                    <div className="flex items-center gap-1 text-[var(--text-muted)] text-sm mt-0.5">
                      <MapPin size={11} />{other.city}
                    </div>
                  )}

                  {other.profile?.mood && (
                    <p className="text-xs mt-1" style={{ color: 'var(--accent-gold)' }}>
                      {MOOD_LABELS[other.profile.mood] || other.profile.mood}
                    </p>
                  )}

                  {reasons.length > 0 && (
                    <ul className="mt-2 space-y-0.5">
                      {reasons.slice(0, 2).map((r, i) => (
                        <li key={i} className="flex items-start gap-1.5 text-xs text-[var(--text-muted)]">
                          <span style={{ color: 'var(--accent-red)' }}>•</span>{r}
                        </li>
                      ))}
                    </ul>
                  )}

                  {match.ai_match_message && (
                    <p className="mt-2 text-xs italic leading-relaxed px-3 py-2 rounded-lg"
                      style={{ background: 'rgba(230,57,70,0.08)', color: 'var(--text-muted)', border: '1px solid rgba(230,57,70,0.15)' }}>
                      {match.ai_match_message}
                    </p>
                  )}

                  <button
                    onClick={() => handleOpenChat(match)}
                    disabled={openingChat === match.id}
                    className="mt-3 flex items-center gap-2 btn-primary text-sm px-4 py-2 disabled:opacity-60"
                  >
                    {openingChat === match.id ? (
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <MessageCircle size={14} />
                    )}
                    Envoyer un message
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
