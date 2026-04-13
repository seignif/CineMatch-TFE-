import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Calendar, CheckCircle, XCircle, Ticket, Clock, MapPin } from 'lucide-react'
import { outingsApi } from '../services/api'
import type { PlannedOuting } from '../types'

type TabKey = 'upcoming' | 'pending' | 'past'

const STATUS_LABELS: Record<string, string> = {
  proposed: 'En attente',
  confirmed: 'Confirmé',
  completed: 'Terminé',
  cancelled: 'Annulé',
}

const STATUS_COLORS: Record<string, string> = {
  proposed: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30',
  confirmed: 'text-green-400 bg-green-400/10 border-green-400/30',
  completed: 'text-blue-400 bg-blue-400/10 border-blue-400/30',
  cancelled: 'text-gray-400 bg-gray-400/10 border-gray-400/30',
}

function formatDatetime(iso: string) {
  return new Date(iso).toLocaleString('fr-BE', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function OutingCard({ outing, onRefresh }: { outing: PlannedOuting; onRefresh: () => void }) {
  const [loading, setLoading] = useState<string | null>(null)

  const runAction = async (fn: () => Promise<unknown>, key: string) => {
    setLoading(key)
    try {
      await fn()
      onRefresh()
    } catch {
      // ignore
    } finally {
      setLoading(null)
    }
  }

  const partner = outing.user_is_proposer ? outing.partner_info : outing.proposer_info
  const userBooked = outing.user_is_proposer ? outing.proposer_booked : outing.partner_booked

  return (
    <div className="glass rounded-2xl overflow-hidden">
      {outing.seance?.film_poster && (
        <div className="h-24 relative overflow-hidden">
          <img
            src={outing.seance.film_poster}
            alt=""
            className="w-full h-full object-cover opacity-40"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[var(--bg-card)] to-transparent" />
        </div>
      )}

      <div className={`p-5 ${outing.seance?.film_poster ? '-mt-6' : ''}`}>
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div>
            <h3 className="font-semibold text-white text-lg leading-tight">
              {outing.seance?.film_title || 'Sortie cinéma'}
            </h3>
            {outing.seance && (
              <p className="text-[var(--text-muted)] text-sm">{outing.seance.cinema_name}</p>
            )}
          </div>
          <span
            className={`text-xs px-2 py-1 rounded-full border shrink-0 ${STATUS_COLORS[outing.status]}`}
          >
            {STATUS_LABELS[outing.status]}
          </span>
        </div>

        {/* Details */}
        <div className="space-y-1.5 mb-4">
          {outing.seance?.showtime && (
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <Clock size={13} />
              {formatDatetime(outing.seance.showtime)}
            </div>
          )}
          {outing.meeting_time && !outing.seance && (
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <Clock size={13} />
              {formatDatetime(outing.meeting_time)}
            </div>
          )}
          {outing.meeting_place && (
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <MapPin size={13} />
              {outing.meeting_place}
            </div>
          )}
          <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
            <span>Avec</span>
            <span className="text-white font-medium">{partner.first_name}</span>
          </div>
        </div>

        {/* Proposal message */}
        {outing.proposal_message && (
          <p
            className="text-xs italic text-[var(--text-muted)] px-3 py-2 rounded-lg mb-4"
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            "{outing.proposal_message}"
          </p>
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-2">
          {/* Confirm: partner only, proposed */}
          {!outing.user_is_proposer && outing.status === 'proposed' && (
            <button
              onClick={() => runAction(() => outingsApi.confirm(outing.id), 'confirm')}
              disabled={loading !== null}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-green-400 bg-green-400/10 hover:bg-green-400/20 transition-colors disabled:opacity-50"
            >
              {loading === 'confirm' ? (
                <div className="w-3 h-3 border border-green-400/30 border-t-green-400 rounded-full animate-spin" />
              ) : (
                <CheckCircle size={13} />
              )}
              Confirmer
            </button>
          )}

          {/* Refuse: partner only, proposed */}
          {!outing.user_is_proposer && outing.status === 'proposed' && (
            <button
              onClick={() => runAction(() => outingsApi.refuse(outing.id), 'refuse')}
              disabled={loading !== null}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-red-400 bg-red-400/10 hover:bg-red-400/20 transition-colors disabled:opacity-50"
            >
              {loading === 'refuse' ? (
                <div className="w-3 h-3 border border-red-400/30 border-t-red-400 rounded-full animate-spin" />
              ) : (
                <XCircle size={13} />
              )}
              Refuser
            </button>
          )}

          {/* Cancel: proposer, proposed|confirmed */}
          {outing.user_is_proposer && ['proposed', 'confirmed'].includes(outing.status) && (
            <button
              onClick={() => runAction(() => outingsApi.cancel(outing.id), 'cancel')}
              disabled={loading !== null}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-red-400 bg-red-400/10 hover:bg-red-400/20 transition-colors disabled:opacity-50"
            >
              {loading === 'cancel' ? (
                <div className="w-3 h-3 border border-red-400/30 border-t-red-400 rounded-full animate-spin" />
              ) : (
                <XCircle size={13} />
              )}
              Annuler
            </button>
          )}

          {/* Mark booked: confirmed, user not yet booked */}
          {outing.status === 'confirmed' && !userBooked && (
            <button
              onClick={() => runAction(() => outingsApi.markBooked(outing.id), 'booked')}
              disabled={loading !== null}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-[var(--accent-gold)] bg-yellow-400/10 hover:bg-yellow-400/20 transition-colors disabled:opacity-50"
            >
              {loading === 'booked' ? (
                <div className="w-3 h-3 border border-yellow-400/30 border-t-yellow-400 rounded-full animate-spin" />
              ) : (
                <Ticket size={13} />
              )}
              J'ai réservé
            </button>
          )}

          {/* External booking link */}
          {outing.seance?.booking_url && outing.status === 'confirmed' && (
            <a
              href={outing.seance.booking_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium btn-primary"
            >
              <Ticket size={13} />
              Réserver sur Kinepolis
            </a>
          )}
        </div>

        {/* Booking status row */}
        {outing.status === 'confirmed' && (
          <div className="flex gap-4 mt-3 text-xs text-[var(--text-muted)]">
            <span>
              {outing.proposer_info.first_name}:{' '}
              {outing.proposer_booked ? '✓ réservé' : '○ pas encore'}
            </span>
            <span>
              {outing.partner_info.first_name}:{' '}
              {outing.partner_booked ? '✓ réservé' : '○ pas encore'}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default function Outings() {
  const [outings, setOutings] = useState<PlannedOuting[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<TabKey>('upcoming')

  const fetchOutings = useCallback(() => {
    outingsApi
      .getAll()
      .then(res => setOutings(res.data))
      .catch(() => setOutings([]))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    fetchOutings()
  }, [fetchOutings])

  const upcoming = outings.filter(o => o.is_upcoming && o.status === 'confirmed')
  const pending = outings.filter(o => o.status === 'proposed')
  const past = outings.filter(
    o =>
      o.status === 'completed' ||
      o.status === 'cancelled' ||
      (o.status === 'confirmed' && !o.is_upcoming),
  )

  const tabs: { key: TabKey; label: string; count: number }[] = [
    { key: 'upcoming', label: 'À venir', count: upcoming.length },
    { key: 'pending', label: 'En attente', count: pending.length },
    { key: 'past', label: 'Passées', count: past.length },
  ]

  const displayed = tab === 'upcoming' ? upcoming : tab === 'pending' ? pending : past

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
          MES <span style={{ color: 'var(--accent-red)' }}>SORTIES</span>
        </h1>
        <p className="text-[var(--text-muted)] mt-1">
          {outings.length} sortie{outings.length !== 1 ? 's' : ''} planifiée
          {outings.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-[var(--accent-red)] text-white'
                : 'glass text-[var(--text-muted)] hover:text-white'
            }`}
          >
            {t.label}
            {t.count > 0 && (
              <span
                className={`text-xs px-1.5 py-0.5 rounded-full ${
                  tab === t.key ? 'bg-white/20' : 'bg-white/10'
                }`}
              >
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {displayed.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <Calendar size={48} className="mb-4 text-[var(--text-muted)]" />
          <h2 className="text-xl font-semibold text-white mb-2">Aucune sortie ici</h2>
          <p className="text-[var(--text-muted)] text-sm mb-6">
            {tab === 'upcoming' && 'Pas encore de sortie confirmée à venir.'}
            {tab === 'pending' && 'Aucune proposition en attente de réponse.'}
            {tab === 'past' && "Vous n'avez pas encore de sorties passées."}
          </p>
          <Link to="/matches" className="btn-primary">
            Voir mes matchs
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {displayed.map(o => (
            <OutingCard key={o.id} outing={o} onRefresh={fetchOutings} />
          ))}
        </div>
      )}
    </div>
  )
}
