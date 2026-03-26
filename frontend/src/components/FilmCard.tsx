import { useNavigate } from 'react-router-dom'
import { Clock, Star } from 'lucide-react'
import type { Film } from '../types'

interface FilmCardProps {
  film: Film
}

function formatDuration(minutes: number | null) {
  if (!minutes) return null
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return `${h}h${m.toString().padStart(2, '0')}`
}

function FilmPoster({ film }: { film: Film }) {
  if (film.poster_url) {
    return (
      <img
        src={film.poster_url}
        alt={film.title}
        className="absolute inset-0 w-full h-full object-cover"
        loading="lazy"
      />
    )
  }
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center p-4"
      style={{ background: 'linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%)' }}>
      <span className="font-display text-3xl text-center leading-tight" style={{ color: 'var(--accent-gold)' }}>
        {film.title}
      </span>
      {film.genres[0] && (
        <span className="mt-2 text-xs text-[var(--text-muted)]">{film.genres[0].name}</span>
      )}
    </div>
  )
}

export default function FilmCard({ film }: FilmCardProps) {
  const navigate = useNavigate()

  return (
    <div
      className="film-card group"
      onClick={() => navigate(`/films/${film.id}`)}
    >
      <FilmPoster film={film} />

      {/* Badges */}
      <div className="absolute top-2 left-2 flex flex-col gap-1 z-10">
        {film.is_future && (
          <span className="badge-red text-xs">Bientôt</span>
        )}
        {film.tmdb_rating && (
          <span className="badge-gold">
            <Star size={10} fill="currentColor" />
            {Number(film.tmdb_rating).toFixed(1)}
          </span>
        )}
      </div>

      {/* Overlay au hover */}
      <div className="overlay z-10">
        <h3 className="font-display text-lg leading-tight text-white">{film.title}</h3>
        <div className="flex items-center gap-2 mt-1 text-[var(--text-muted)] text-xs">
          {film.duration && (
            <span className="flex items-center gap-1">
              <Clock size={11} />
              {formatDuration(film.duration)}
            </span>
          )}
          {film.genres.slice(0, 2).map(g => (
            <span key={g.id} className="px-1.5 py-0.5 rounded"
              style={{ background: 'rgba(255,255,255,0.1)' }}>
              {g.name}
            </span>
          ))}
        </div>
        {film.short_synopsis && (
          <p className="mt-2 text-xs text-[var(--text-muted)] line-clamp-2">{film.short_synopsis}</p>
        )}
        <button className="mt-3 w-full py-1.5 rounded-lg text-xs font-medium text-white transition-colors"
          style={{ background: 'var(--accent-red)' }}>
          Voir le film
        </button>
      </div>

      {/* Titre toujours visible en bas (sans hover) */}
      <div className="absolute bottom-0 left-0 right-0 p-3 z-10 group-hover:opacity-0 transition-opacity"
        style={{ background: 'linear-gradient(to top, rgba(10,10,15,0.9) 0%, transparent 100%)' }}>
        <p className="text-sm font-medium text-white line-clamp-1">{film.title}</p>
      </div>
    </div>
  )
}
