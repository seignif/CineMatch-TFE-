import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Clock, Star, Play, Calendar, X } from 'lucide-react'
import { filmsApi } from '../services/api'
import SeanceCard from '../components/SeanceCard'
import type { Film, Seance } from '../types'

function formatDuration(minutes: number | null) {
  if (!minutes) return null
  return `${Math.floor(minutes / 60)}h${(minutes % 60).toString().padStart(2, '0')}`
}

function formatDate(isoDate: string | null) {
  if (!isoDate) return null
  const d = new Date(isoDate)
  return d.toLocaleDateString('fr-BE', { year: 'numeric', month: 'long', day: 'numeric' })
}

function TrailerModal({ youtubeKey, onClose }: { youtubeKey: string; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.9)' }}
      onClick={onClose}
    >
      <div className="relative w-full max-w-4xl" onClick={e => e.stopPropagation()}>
        <button onClick={onClose}
          className="absolute -top-10 right-0 text-white hover:text-[var(--accent-red)] transition-colors">
          <X size={24} />
        </button>
        <div className="relative" style={{ paddingBottom: '56.25%' }}>
          <iframe
            className="absolute inset-0 w-full h-full rounded-xl"
            src={`https://www.youtube.com/embed/${youtubeKey}?autoplay=1`}
            allow="autoplay; encrypted-media"
            allowFullScreen
          />
        </div>
      </div>
    </div>
  )
}

export default function FilmDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [film, setFilm] = useState<Film | null>(null)
  const [seances, setSeances] = useState<Seance[]>([])
  const [loading, setLoading] = useState(true)
  const [showTrailer, setShowTrailer] = useState(false)
  const [selectedCinema, setSelectedCinema] = useState<string>('all')

  useEffect(() => {
    if (!id) return
    const filmId = parseInt(id)
    Promise.all([
      filmsApi.getById(filmId),
      filmsApi.getSeances(filmId),
    ]).then(([filmRes, seancesRes]) => {
      setFilm(filmRes.data)
      setSeances(seancesRes.data)
    }).catch(() => navigate('/films'))
      .finally(() => setLoading(false))
  }, [id, navigate])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-[var(--accent-red)] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[var(--text-muted)] text-sm">Chargement...</p>
        </div>
      </div>
    )
  }

  if (!film) return null

  const cinemas = Array.from(new Set(seances.map(s => s.cinema.name)))
  const filteredSeances = selectedCinema === 'all'
    ? seances
    : seances.filter(s => s.cinema.name === selectedCinema)

  // Group seances by date
  const seancesByDate: Record<string, Seance[]> = {}
  filteredSeances.forEach(s => {
    const date = new Date(s.showtime).toLocaleDateString('fr-BE', {
      weekday: 'long', day: 'numeric', month: 'long'
    })
    if (!seancesByDate[date]) seancesByDate[date] = []
    seancesByDate[date].push(s)
  })

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <div className="relative h-[70vh] min-h-[500px]">
        {film.backdrop_url ? (
          <img src={film.backdrop_url} alt={film.title}
            className="absolute inset-0 w-full h-full object-cover" />
        ) : film.poster_url ? (
          <img src={film.poster_url} alt={film.title}
            className="absolute inset-0 w-full h-full object-cover object-top blur-sm scale-105" />
        ) : (
          <div className="absolute inset-0"
            style={{ background: 'linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%)' }} />
        )}
        {/* Gradient overlay */}
        <div className="absolute inset-0"
          style={{ background: 'linear-gradient(to bottom, rgba(10,10,15,0.3) 0%, rgba(10,10,15,0.6) 50%, rgba(10,10,15,1) 100%)' }} />

        {/* Back button */}
        <button
          onClick={() => navigate(-1)}
          className="absolute top-6 left-6 flex items-center gap-2 glass px-4 py-2 rounded-lg text-sm hover:bg-white/10 transition-colors"
        >
          <ArrowLeft size={16} />
          Retour
        </button>

        {/* Film info */}
        <div className="absolute bottom-0 left-0 right-0 p-6 max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row gap-6 items-end">
            {/* Poster */}
            {film.poster_url && (
              <div className="hidden md:block shrink-0 w-40 rounded-xl overflow-hidden shadow-2xl border border-white/10">
                <img src={film.poster_url} alt={film.title} className="w-full" />
              </div>
            )}

            {/* Infos */}
            <div className="flex-1">
              <div className="flex flex-wrap gap-2 mb-3">
                {film.genres.map(g => (
                  <span key={g.id} className="text-xs px-2 py-1 rounded"
                    style={{ background: 'rgba(255,255,255,0.1)', color: 'var(--text-muted)' }}>
                    {g.name}
                  </span>
                ))}
                {film.is_future && <span className="badge-red">Bientôt</span>}
              </div>

              <h1 className="font-display text-5xl md:text-6xl tracking-wider text-white leading-none">
                {film.title}
              </h1>

              <div className="flex flex-wrap items-center gap-4 mt-3">
                {film.tmdb_rating && (
                  <span className="badge-gold text-sm">
                    <Star size={13} fill="currentColor" />
                    {Number(film.tmdb_rating).toFixed(1)} TMDb
                  </span>
                )}
                {film.duration && (
                  <span className="flex items-center gap-1.5 text-sm text-[var(--text-muted)]">
                    <Clock size={14} />
                    {formatDuration(film.duration)}
                  </span>
                )}
                {film.release_date && (
                  <span className="flex items-center gap-1.5 text-sm text-[var(--text-muted)]">
                    <Calendar size={14} />
                    {formatDate(film.release_date)}
                  </span>
                )}
              </div>

              {film.trailer_youtube_key && (
                <button
                  onClick={() => setShowTrailer(true)}
                  className="mt-4 flex items-center gap-2 btn-primary"
                >
                  <Play size={16} fill="white" />
                  Bande-annonce
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Synopsis */}
        {(film.synopsis || film.short_synopsis) && (
          <div className="mb-10">
            <h2 className="font-display text-2xl tracking-wider text-white mb-3">SYNOPSIS</h2>
            <p className="text-[var(--text-muted)] leading-relaxed max-w-3xl">
              {film.synopsis || film.short_synopsis}
            </p>
          </div>
        )}

        {/* Séances */}
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <h2 className="font-display text-2xl tracking-wider text-white">
              SÉANCES DISPONIBLES
              <span className="text-[var(--text-muted)] text-lg ml-3 font-sans font-normal normal-case">
                ({seances.length} séance{seances.length !== 1 ? 's' : ''})
              </span>
            </h2>

            {cinemas.length > 1 && (
              <select
                value={selectedCinema}
                onChange={e => setSelectedCinema(e.target.value)}
                className="input-field w-auto text-sm"
              >
                <option value="all">Tous les cinémas</option>
                {cinemas.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            )}
          </div>

          {seances.length === 0 ? (
            <div className="glass rounded-xl p-8 text-center">
              <p className="text-[var(--text-muted)]">Aucune séance disponible pour ce film.</p>
            </div>
          ) : Object.keys(seancesByDate).length === 0 ? (
            <div className="glass rounded-xl p-8 text-center">
              <p className="text-[var(--text-muted)]">Aucune séance pour ce cinéma.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(seancesByDate).map(([date, dateSeances]) => (
                <div key={date}>
                  <h3 className="text-sm font-medium text-[var(--accent-gold)] uppercase tracking-wider mb-3 font-mono">
                    {date}
                  </h3>
                  <div className="space-y-2">
                    {dateSeances.map(s => (
                      <SeanceCard key={s.id} seance={s} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Trailer modal */}
      {showTrailer && film.trailer_youtube_key && (
        <TrailerModal youtubeKey={film.trailer_youtube_key} onClose={() => setShowTrailer(false)} />
      )}
    </div>
  )
}
