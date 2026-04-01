import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import TinderCard from 'react-tinder-card'
import { X, Star, Heart, MapPin } from 'lucide-react'
import { matchingApi, chatApi } from '../services/api'
import type { Candidate, Match } from '../types'

const MOOD_LABELS: Record<string, string> = {
  rire: 'Envie de rire',
  reflechir: 'Besoin de réfléchir',
  emu: "Envie d'être ému",
  adrenaline: "Besoin d'adrénaline",
}

function ScoreBar({ score }: { score: number }) {
  const color = score >= 70 ? '#4ade80' : score >= 50 ? '#facc15' : '#E63946'
  return (
    <div className="w-full bg-white/10 rounded-full h-1.5 mt-1">
      <div className="h-1.5 rounded-full transition-all" style={{ width: `${score}%`, background: color }} />
    </div>
  )
}

function MatchModal({ match, onClose }: { match: Match; onClose: () => void }) {
  const navigate = useNavigate()
  const other = match.other_user

  const handleChat = async () => {
    try {
      const res = await chatApi.createConversation(match.id)
      navigate(`/chat/${res.data.id}`)
    } catch {
      navigate('/matches')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4"
      style={{ background: 'rgba(0,0,0,0.85)' }}>
      <div className="glass rounded-2xl p-8 max-w-sm w-full text-center">
        <div className="text-5xl mb-4">🎉</div>
        <h2 className="font-display text-3xl tracking-wider mb-1">
          C&apos;EST UN <span style={{ color: 'var(--accent-red)' }}>MATCH</span> !
        </h2>
        <p className="text-[var(--text-muted)] text-sm mb-4">
          Toi et {other.first_name} vous avez matché !
        </p>
        <div className="px-4 py-3 rounded-xl mb-4 text-sm text-left leading-relaxed"
          style={{ background: 'rgba(230,57,70,0.1)', border: '1px solid rgba(230,57,70,0.2)' }}>
          {match.ai_match_message || `Super compatibilité avec ${other.first_name} !`}
        </div>
        <div className="text-4xl font-bold mb-1" style={{ color: 'var(--accent-gold)' }}>
          {match.score_compatibilite}%
        </div>
        <p className="text-xs text-[var(--text-muted)] mb-6">Compatibilité</p>
        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 btn-secondary py-3 text-sm">
            Continuer à swiper
          </button>
          <button onClick={handleChat} className="flex-1 btn-primary py-3 text-sm">
            Envoyer un message
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Matching() {
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(true)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [matchResult, setMatchResult] = useState<Match | null>(null)
  const [swiping, setSwiping] = useState(false)
  const cardRefs = useRef<Record<number, { swipe: (dir: string) => Promise<void> }>>({})

  useEffect(() => {
    matchingApi.getCandidates()
      .then(res => {
        setCandidates(res.data)
        setCurrentIndex(res.data.length - 1)
      })
      .catch(() => setCandidates([]))
      .finally(() => setLoading(false))
  }, [])

  const doSwipe = useCallback(async (candidate: Candidate, action: 'like' | 'pass' | 'superlike') => {
    if (swiping) return
    setSwiping(true)
    try {
      const res = await matchingApi.swipe(candidate.id, action)
      if (res.data.match) setMatchResult(res.data.match)
    } catch { /* ignore */ }
    setCurrentIndex(prev => prev - 1)
    setSwiping(false)
  }, [swiping])

  const onSwipe = useCallback((dir: string, candidate: Candidate) => {
    if (dir === 'right') doSwipe(candidate, 'like')
    else if (dir === 'left') doSwipe(candidate, 'pass')
    else if (dir === 'up') doSwipe(candidate, 'superlike')
  }, [doSwipe])

  const triggerSwipe = (action: 'like' | 'pass' | 'superlike') => {
    const candidate = candidates[currentIndex]
    if (!candidate || swiping) return
    const dir = action === 'like' ? 'right' : action === 'pass' ? 'left' : 'up'
    cardRefs.current[candidate.id]?.swipe(dir)
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

  if (candidates.length === 0 || currentIndex < 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center text-center px-4">
        {matchResult && (
          <MatchModal match={matchResult} onClose={() => setMatchResult(null)} />
        )}
        <div className="text-6xl mb-4">🎬</div>
        <h2 className="font-display text-3xl tracking-wider text-white mb-2">C&apos;EST TOUT !</h2>
        <p className="text-[var(--text-muted)] text-sm">
          Vous avez vu tous les profils disponibles.<br />
          Revenez demain pour de nouveaux profils !
        </p>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-8">
      {matchResult && (
        <MatchModal match={matchResult} onClose={() => setMatchResult(null)} />
      )}
      <div className="w-full max-w-sm">
        <div className="mb-4 text-center">
          <h1 className="font-display text-3xl tracking-wider text-white">MATCHING</h1>
          <p className="text-[var(--text-muted)] text-xs mt-1">
            {currentIndex + 1} profil{currentIndex > 0 ? 's' : ''} restant{currentIndex > 0 ? 's' : ''}
          </p>
        </div>

        <div className="relative h-[480px] w-full">
          {candidates.slice(0, currentIndex + 1).map((c, i) => {
            const isTop = i === currentIndex
            return (
              <TinderCard
                key={c.id}
                ref={(el) => { if (el) cardRefs.current[c.id] = el as { swipe: (dir: string) => Promise<void> } }}
                onSwipe={(dir) => isTop && onSwipe(dir, c)}
                preventSwipe={['down']}
                className="absolute w-full"
              >
                <div className="w-full rounded-2xl overflow-hidden select-none cursor-grab"
                  style={{ background: 'var(--bg-card)', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <div className="h-72 relative">
                    {c.profile?.profile_picture ? (
                      <img src={c.profile.profile_picture} alt={c.first_name}
                        className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-7xl font-bold"
                        style={{ background: 'var(--bg-secondary)', color: 'var(--accent-red)' }}>
                        {c.first_name?.[0]?.toUpperCase() ?? '?'}
                      </div>
                    )}
                    <div className="absolute top-3 right-3 px-3 py-1 rounded-full text-sm font-bold"
                      style={{ background: 'rgba(0,0,0,0.7)', color: 'var(--accent-gold)' }}>
                      {c.score}%
                    </div>
                  </div>
                  <div className="p-4">
                    <h3 className="text-xl font-semibold text-white mb-0.5">
                      {c.first_name}{calcAge(c.date_of_birth) ? `, ${calcAge(c.date_of_birth)} ans` : ''}
                    </h3>
                    {c.city && (
                      <div className="flex items-center gap-1 text-[var(--text-muted)] text-sm mb-2">
                        <MapPin size={12} />{c.city}
                      </div>
                    )}
                    <ScoreBar score={c.score} />
                    {c.profile?.mood && (
                      <p className="text-xs mt-2" style={{ color: 'var(--accent-gold)' }}>
                        {MOOD_LABELS[c.profile.mood] || c.profile.mood}
                      </p>
                    )}
                    {c.reasons.length > 0 && (
                      <ul className="mt-2 space-y-1">
                        {c.reasons.slice(0, 2).map((r, idx) => (
                          <li key={idx} className="flex items-start gap-1.5 text-xs text-[var(--text-muted)]">
                            <span style={{ color: 'var(--accent-red)' }}>•</span>{r}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </TinderCard>
            )
          })}
        </div>

        <div className="flex items-center justify-center gap-5 mt-6">
          <button onClick={() => triggerSwipe('pass')} disabled={swiping}
            className="w-14 h-14 rounded-full flex items-center justify-center transition-transform hover:scale-110 disabled:opacity-50"
            style={{ background: 'rgba(255,255,255,0.1)', border: '2px solid rgba(255,255,255,0.15)' }}>
            <X size={22} className="text-white" />
          </button>
          <button onClick={() => triggerSwipe('superlike')} disabled={swiping}
            className="w-12 h-12 rounded-full flex items-center justify-center transition-transform hover:scale-110 disabled:opacity-50"
            style={{ background: 'rgba(250,204,21,0.15)', border: '2px solid rgba(250,204,21,0.4)' }}>
            <Star size={18} style={{ color: 'var(--accent-gold)' }} />
          </button>
          <button onClick={() => triggerSwipe('like')} disabled={swiping}
            className="w-14 h-14 rounded-full flex items-center justify-center transition-transform hover:scale-110 disabled:opacity-50"
            style={{ background: 'rgba(230,57,70,0.2)', border: '2px solid rgba(230,57,70,0.4)' }}>
            <Heart size={22} style={{ color: 'var(--accent-red)' }} />
          </button>
        </div>
        <p className="text-center text-xs text-[var(--text-muted)] mt-4">
          Swipe gauche = passer · Swipe droite = liker · Haut = super like
        </p>
      </div>
    </div>
  )
}
