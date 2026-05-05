import { useState, useEffect, useCallback } from 'react'
import { Search, SlidersHorizontal, X, Sparkles, ChevronDown } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { filmsApi, recommendationsApi } from '../services/api'
import { useAuthStore } from '../store/authStore'
import FilmCard from '../components/FilmCard'
import type { Film, PaginatedResponse, FilmRecommendation } from '../types'

const RATINGS = [
  { value: 6, label: '≥ 6' },
  { value: 7, label: '≥ 7' },
  { value: 8, label: '≥ 8' },
]

function SkeletonCard() {
  return (
    <div className="rounded-xl animate-pulse" style={{ aspectRatio: '2/3', background: 'var(--bg-card)' }} />
  )
}

export default function Films() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { user } = useAuthStore()

  // Tout l'état de navigation vit dans l'URL pour que le bouton retour restaure la position exacte
  const isFuture = searchParams.get('tab') === 'bientot'
  const page = parseInt(searchParams.get('page') || '1', 10)
  const search = searchParams.get('search') || ''
  const selectedGenre = searchParams.get('genre') || ''
  const selectedRating = searchParams.get('rating') ? parseInt(searchParams.get('rating')!, 10) : null
  const showEvents = searchParams.get('events') === '1'
  const selectedMaxAge = searchParams.get('max_age') || ''
  const selectedLang = searchParams.get('lang') || ''

  const [films, setFilms] = useState<Film[]>([])
  const [loading, setLoading] = useState(true)
  const [totalCount, setTotalCount] = useState(0)
  const [searchInput, setSearchInput] = useState(search)
  const [recommendations, setRecommendations] = useState<FilmRecommendation[]>([])
  const [showFilters, setShowFilters] = useState(false)
  const [genres, setGenres] = useState<string[]>([])

  const updateParams = (updates: Record<string, string | null>) => {
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      Object.entries(updates).forEach(([k, v]) => {
        if (v === null || v === '' || v === '0') next.delete(k)
        else next.set(k, v)
      })
      // Réinitialiser la page si autre chose que la page change
      const pageKeys = ['page']
      if (Object.keys(updates).some(k => !pageKeys.includes(k))) next.delete('page')
      return next
    }, { replace: false })
  }

  const currentMood = user?.profile?.mood
  useEffect(() => {
    recommendationsApi.getRecommendations()
      .then(res => setRecommendations(res.data))
      .catch(() => {})
  }, [currentMood])

  useEffect(() => {
    filmsApi.getGenres()
      .then(res => setGenres(res.data))
      .catch(() => {})
  }, [])

  const fetchFilms = useCallback(async () => {
    setLoading(true)
    try {
      const res = await filmsApi.getAll({
        search: search || undefined,
        is_future: isFuture,
        page,
        genre: selectedGenre || undefined,
        min_rating: selectedRating ?? undefined,
        show_events: showEvents ? 'true' : 'false',
        max_age: selectedMaxAge || undefined,
        seance_lang: selectedLang || undefined,
      })
      const data: PaginatedResponse<Film> = res.data
      setFilms(data.results)
      setTotalCount(data.count)
    } catch {
      setFilms([])
    } finally {
      setLoading(false)
    }
  }, [search, isFuture, page, selectedGenre, selectedRating, showEvents, selectedMaxAge, selectedLang])

  useEffect(() => {
    fetchFilms()
  }, [fetchFilms])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    updateParams({ search: searchInput || null })
  }

  const clearSearch = () => {
    setSearchInput('')
    updateParams({ search: null })
  }

  const clearFilters = () => {
    updateParams({ genre: null, rating: null, events: null, max_age: null, lang: null })
  }

  const activeFilterCount = [
    selectedGenre,
    selectedRating !== null,
    showEvents,
    selectedMaxAge !== '',
    selectedLang !== '',
  ].filter(Boolean).length
  const totalPages = Math.ceil(totalCount / 20)

  return (
    <div className="min-h-screen px-4 py-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="font-display text-5xl tracking-wider text-white">
          {isFuture ? 'PROCHAINEMENT' : 'À L\'AFFICHE'}
        </h1>
        <p className="text-[var(--text-muted)] mt-1">
          {totalCount} film{totalCount > 1 ? 's' : ''} disponible{totalCount > 1 ? 's' : ''}
        </p>
      </div>

      {/* Recommandations */}
      {recommendations.length > 0 && !search && (
        <div className="mb-10">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles size={16} style={{ color: 'var(--accent-gold)' }} />
            <h2 className="text-sm font-medium uppercase tracking-wider" style={{ color: 'var(--accent-gold)' }}>
              Films pour vous
            </h2>
          </div>
          <div className="flex gap-4 overflow-x-auto pb-2 -mx-1 px-1" style={{ scrollbarWidth: 'none' }}>
            {recommendations.map(({ film, reasons }) => (
              <button key={film.id} onClick={() => navigate(`/films/${film.id}`)}
                className="shrink-0 w-36 text-left group">
                <div className="w-36 h-52 rounded-xl overflow-hidden mb-2 relative"
                  style={{ border: '1px solid rgba(255,215,0,0.2)' }}>
                  {film.poster_url
                    ? <img src={film.poster_url} alt={film.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                    : <div className="w-full h-full flex items-center justify-center text-3xl"
                        style={{ background: 'var(--bg-card)' }}>🎬</div>
                  }
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                <p className="text-white text-xs font-medium leading-tight truncate">{film.title}</p>
                {reasons[0] && (
                  <p className="text-xs mt-0.5 leading-tight" style={{ color: 'var(--accent-gold)' }}>
                    {reasons[0]}
                  </p>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Barre de contrôles */}
      <div className="flex flex-col sm:flex-row gap-3 mb-3">
        <form onSubmit={handleSearch} className="flex-1 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input
            type="text"
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            placeholder="Rechercher un film..."
            className="input-field pl-9 pr-9"
          />
          {searchInput && (
            <button type="button" onClick={clearSearch}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-white">
              <X size={14} />
            </button>
          )}
        </form>

        <div className="flex items-center gap-1 glass rounded-lg p-1 shrink-0">
          <button
            onClick={() => setSearchParams({})}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              !isFuture ? 'bg-[var(--accent-red)] text-white' : 'text-[var(--text-muted)] hover:text-white'
            }`}
          >
            À l'affiche
          </button>
          <button
            onClick={() => setSearchParams({ tab: 'bientot' })}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              isFuture ? 'bg-[var(--accent-red)] text-white' : 'text-[var(--text-muted)] hover:text-white'
            }`}
          >
            Bientôt
          </button>
        </div>

        <button
          onClick={() => setShowFilters(f => !f)}
          className={`flex items-center gap-2 shrink-0 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            showFilters || activeFilterCount > 0
              ? 'bg-[var(--accent-red)] text-white'
              : 'btn-secondary'
          }`}
        >
          <SlidersHorizontal size={15} />
          Filtres
          {activeFilterCount > 0 && (
            <span className="w-5 h-5 rounded-full bg-white/20 text-xs flex items-center justify-center font-bold">
              {activeFilterCount}
            </span>
          )}
          <ChevronDown size={14} className={`transition-transform ${showFilters ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {/* Panneau de filtres */}
      {showFilters && (
        <div className="glass rounded-xl p-5 mb-5 space-y-5">
          {/* Genre */}
          <div>
            <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-2">Genre</p>
            <div className="flex flex-wrap gap-2">
              {genres.map(g => (
                <button
                  key={g}
                  onClick={() => updateParams({ genre: selectedGenre === g ? null : g })}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                    selectedGenre === g
                      ? 'bg-[var(--accent-red)] text-white'
                      : 'glass text-[var(--text-muted)] hover:text-white'
                  }`}
                >
                  {g}
                </button>
              ))}
            </div>
          </div>

          {/* Note TMDb */}
          <div>
            <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-2">Note TMDb minimum</p>
            <div className="flex gap-2">
              {RATINGS.map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => updateParams({ rating: selectedRating === value ? null : String(value) })}
                  className={`px-4 py-1.5 rounded-full text-xs font-medium transition-colors ${
                    selectedRating === value
                      ? 'bg-[var(--accent-red)] text-white'
                      : 'glass text-[var(--text-muted)] hover:text-white'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Classification âge */}
          <div>
            <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-2">Classification âge</p>
            <div className="flex flex-wrap gap-2">
              {[
                { label: 'Tous', value: '' },
                { label: '+6', value: '6' },
                { label: '+12', value: '12' },
                { label: '+16', value: '16' },
                { label: '+18', value: '18' },
              ].map(opt => (
                <button
                  key={opt.value}
                  onClick={() => updateParams({ max_age: selectedMaxAge === opt.value ? null : opt.value || null })}
                  className={`px-4 py-1.5 rounded-full text-xs font-medium transition-colors ${
                    selectedMaxAge === opt.value
                      ? 'bg-[var(--accent-red)] text-white'
                      : 'glass text-[var(--text-muted)] hover:text-white'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Langue des séances */}
          <div>
            <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-2">Langue des séances</p>
            <div className="flex gap-2">
              {[
                { value: '', label: 'Toutes' },
                { value: 'vf', label: 'VF / NL' },
                { value: 'vo', label: 'VO / VOST' },
              ].map(opt => (
                <button
                  key={opt.value}
                  onClick={() => updateParams({ lang: selectedLang === opt.value ? null : opt.value || null })}
                  className={`px-4 py-1.5 rounded-full text-xs font-medium transition-colors ${
                    selectedLang === opt.value
                      ? 'bg-[var(--accent-red)] text-white'
                      : 'glass text-[var(--text-muted)] hover:text-white'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Toggle événements spéciaux */}
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={showEvents}
              onChange={e => updateParams({ events: e.target.checked ? '1' : null })}
              className="w-4 h-4 accent-[var(--accent-red)]"
            />
            <span className="text-sm text-[var(--text-muted)]">
              Afficher opéras, concerts et événements spéciaux
            </span>
          </label>

          {activeFilterCount > 0 && (
            <button onClick={clearFilters}
              className="text-xs text-[var(--text-muted)] hover:text-white underline transition-colors">
              Réinitialiser les filtres
            </button>
          )}
        </div>
      )}

      {/* Badges filtres actifs */}
      {(search || activeFilterCount > 0) && (
        <div className="flex flex-wrap items-center gap-2 mb-5">
          {search && (
            <span className="flex items-center gap-1 px-3 py-1 rounded-full text-xs cursor-pointer"
              style={{ background: 'rgba(230,57,70,0.15)', border: '1px solid rgba(230,57,70,0.3)', color: 'var(--text-primary)' }}
              onClick={clearSearch}>
              "{search}" <X size={10} />
            </span>
          )}
          {selectedGenre && (
            <span className="flex items-center gap-1 px-3 py-1 rounded-full text-xs cursor-pointer"
              style={{ background: 'rgba(230,57,70,0.15)', border: '1px solid rgba(230,57,70,0.3)', color: 'var(--text-primary)' }}
              onClick={() => updateParams({ genre: null })}>
              {selectedGenre} <X size={10} />
            </span>
          )}

          {selectedRating !== null && (
            <span className="flex items-center gap-1 px-3 py-1 rounded-full text-xs cursor-pointer"
              style={{ background: 'rgba(230,57,70,0.15)', border: '1px solid rgba(230,57,70,0.3)', color: 'var(--text-primary)' }}
              onClick={() => updateParams({ rating: null })}>
              ★ ≥ {selectedRating} <X size={10} />
            </span>
          )}
        </div>
      )}

      {/* Grille */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {Array.from({ length: 20 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : films.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="text-6xl mb-4">🎬</div>
          <p className="text-white font-semibold text-lg">Aucun film trouvé</p>
          <p className="text-[var(--text-muted)] text-sm mt-1">Essaie d'autres filtres ou termes de recherche</p>
          {(search || activeFilterCount > 0) && (
            <button onClick={() => { clearSearch(); clearFilters() }} className="btn-primary mt-6">
              Réinitialiser les filtres
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {films.map(film => (
            <FilmCard key={film.id} film={film} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && !loading && (
        <div className="flex items-center justify-center gap-2 mt-10">
          <button
            disabled={page === 1}
            onClick={() => updateParams({ page: String(page - 1) })}
            className="btn-secondary px-4 py-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ← Précédent
          </button>
          <span className="text-sm text-[var(--text-muted)] px-4">
            {page} / {totalPages}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => updateParams({ page: String(page + 1) })}
            className="btn-secondary px-4 py-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Suivant →
          </button>
        </div>
      )}
    </div>
  )
}
