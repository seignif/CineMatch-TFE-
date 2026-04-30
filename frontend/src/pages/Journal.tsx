import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Trash2, Star, BookOpen, TrendingUp } from 'lucide-react'
import { watchedApi } from '../services/api'
import type { WatchedFilm, JournalStats } from '../types'
import { mediaUrl } from '../utils/media'

function StarRating({ rating, onChange }: { rating: number; onChange?: (r: number) => void }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map(n => (
        <button key={n} type="button" onClick={() => onChange?.(n)}
          className={onChange ? 'cursor-pointer' : 'cursor-default'}
          style={{ color: n <= rating ? 'var(--accent-gold)' : 'rgba(255,255,255,0.2)', fontSize: '18px' }}>
          ★
        </button>
      ))}
    </div>
  )
}

export default function Journal() {
  const navigate = useNavigate()
  const [entries, setEntries] = useState<WatchedFilm[]>([])
  const [stats, setStats] = useState<JournalStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [sortBy, setSortBy] = useState<'date' | 'rating_desc' | 'rating_asc'>('date')

  useEffect(() => {
    Promise.all([
      watchedApi.getAll(),
      watchedApi.getStats(),
    ]).then(([entriesRes, statsRes]) => {
      setEntries(entriesRes.data.results ?? entriesRes.data)
      setStats(statsRes.data)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleDelete = async (id: number) => {
    if (!confirm('Supprimer ce film de votre journal ?')) return
    await watchedApi.delete(id)
    setEntries(prev => prev.filter(e => e.id !== id))
  }

  const sorted = [...entries].sort((a, b) => {
    if (sortBy === 'date') {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    }
    const ra = a.rating ?? 0
    const rb = b.rating ?? 0
    return sortBy === 'rating_desc' ? rb - ra : ra - rb
  })

  return (
    <div className="min-h-screen max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="font-display text-5xl tracking-wider text-white">MON JOURNAL</h1>
        <p className="text-[var(--text-muted)] mt-1">Films vus au cinéma</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: 'Films vus', value: stats.total_watched, icon: BookOpen },
            { label: 'Note moyenne', value: stats.average_rating ? `${stats.average_rating} ★` : '—', icon: Star },
            { label: 'Genre favori', value: stats.top_genre || '—', icon: TrendingUp },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label} className="glass rounded-xl p-4 text-center">
              <Icon size={20} className="mx-auto mb-2" style={{ color: 'var(--accent-gold)' }} />
              <div className="text-xl font-bold text-white">{value}</div>
              <div className="text-xs text-[var(--text-muted)] mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tri */}
      <div className="flex gap-2 mb-6">
        {[
          { value: 'date', label: 'Plus récents' },
          { value: 'rating_desc', label: 'Mieux notés' },
          { value: 'rating_asc', label: 'Moins bien notés' },
        ].map(opt => (
          <button key={opt.value} onClick={() => setSortBy(opt.value as typeof sortBy)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              sortBy === opt.value ? 'bg-[var(--accent-red)] text-white' : 'glass text-[var(--text-muted)] hover:text-white'
            }`}>
            {opt.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="glass rounded-xl p-4 animate-pulse h-24" />
          ))}
        </div>
      ) : sorted.length === 0 ? (
        <div className="text-center py-20">
          <div className="text-5xl mb-4">📔</div>
          <p className="text-white font-semibold text-lg">Journal vide</p>
          <p className="text-[var(--text-muted)] text-sm mt-1 mb-6">
            Commencez à noter les films vus en cliquant sur "J'ai vu ce film" depuis une fiche film.
          </p>
          <button onClick={() => navigate('/')} className="btn-primary">
            Découvrir les films
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {sorted.map(entry => (
            <div key={entry.id} className="glass rounded-xl p-4 flex gap-4">
              {entry.film_info?.poster_url ? (
                <img
                  src={mediaUrl(entry.film_info.poster_url) || entry.film_info.poster_url}
                  alt={entry.film_info.title}
                  className="w-14 h-20 object-cover rounded-lg shrink-0 cursor-pointer"
                  onClick={() => entry.film_info && navigate(`/films/${entry.film_info.id}`)}
                />
              ) : (
                <div className="w-14 h-20 rounded-lg shrink-0 flex items-center justify-center text-2xl"
                  style={{ background: 'rgba(255,255,255,0.05)' }}>
                  ?
                </div>
              )}
              <div className="flex-1 min-w-0">
                <h3
                  className="text-white font-medium truncate cursor-pointer hover:text-[var(--accent-red)] transition-colors"
                  onClick={() => entry.film_info && navigate(`/films/${entry.film_info.id}`)}>
                  {entry.film_info?.title ?? 'Film inconnu'}
                </h3>
                {entry.rating !== null && (
                  <StarRating rating={entry.rating} />
                )}
                {entry.watched_date && (
                  <p className="text-xs text-[var(--text-muted)] mt-1">
                    Vu le {new Date(entry.watched_date).toLocaleDateString('fr-BE', { day: 'numeric', month: 'long', year: 'numeric' })}
                  </p>
                )}
                {entry.review && (
                  <p className="text-sm text-[var(--text-muted)] mt-1 italic line-clamp-2">
                    "{entry.review}"
                  </p>
                )}
                <div className="flex items-center gap-1 mt-1">
                  <span className="text-xs" style={{ color: entry.is_public ? '#4ade80' : 'var(--text-muted)' }}>
                    {entry.is_public ? 'Avis public' : 'Privé'}
                  </span>
                </div>
              </div>
              <button onClick={() => handleDelete(entry.id)}
                className="shrink-0 p-2 rounded-lg transition-colors hover:bg-red-500/10"
                style={{ color: 'var(--text-muted)' }}>
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
