import { useState, useEffect, useCallback } from 'react'
import { Search, SlidersHorizontal, X } from 'lucide-react'
import { filmsApi } from '../services/api'
import FilmCard from '../components/FilmCard'
import type { Film, PaginatedResponse } from '../types'

function SkeletonCard() {
  return (
    <div className="rounded-xl animate-pulse" style={{ aspectRatio: '2/3', background: 'var(--bg-card)' }} />
  )
}

export default function Films() {
  const [films, setFilms] = useState<Film[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [isFuture, setIsFuture] = useState(false)
  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [searchInput, setSearchInput] = useState('')

  const fetchFilms = useCallback(async () => {
    setLoading(true)
    try {
      const res = await filmsApi.getAll({
        search: search || undefined,
        is_future: isFuture,
        page,
      })
      const data: PaginatedResponse<Film> = res.data
      setFilms(data.results)
      setTotalCount(data.count)
    } catch {
      setFilms([])
    } finally {
      setLoading(false)
    }
  }, [search, isFuture, page])

  useEffect(() => {
    setPage(1)
  }, [search, isFuture])

  useEffect(() => {
    fetchFilms()
  }, [fetchFilms])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearch(searchInput)
  }

  const clearSearch = () => {
    setSearchInput('')
    setSearch('')
  }

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

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-3 mb-8">
        {/* Search */}
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

        {/* Toggle à l'affiche / prochainement */}
        <div className="flex items-center gap-1 glass rounded-lg p-1 shrink-0">
          <button
            onClick={() => setIsFuture(false)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              !isFuture ? 'bg-[var(--accent-red)] text-white' : 'text-[var(--text-muted)] hover:text-white'
            }`}
          >
            À l'affiche
          </button>
          <button
            onClick={() => setIsFuture(true)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              isFuture ? 'bg-[var(--accent-red)] text-white' : 'text-[var(--text-muted)] hover:text-white'
            }`}
          >
            Bientôt
          </button>
        </div>

        <button className="flex items-center gap-2 btn-secondary shrink-0">
          <SlidersHorizontal size={15} />
          Filtres
        </button>
      </div>

      {/* Actif search */}
      {search && (
        <div className="flex items-center gap-2 mb-4">
          <span className="text-sm text-[var(--text-muted)]">Résultats pour :</span>
          <span className="badge-red cursor-pointer" onClick={clearSearch}>
            {search} <X size={10} className="inline ml-1" />
          </span>
        </div>
      )}

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {Array.from({ length: 20 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : films.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <span className="font-display text-6xl text-[var(--accent-red)] mb-4">404</span>
          <p className="text-white font-medium text-lg">Aucun film trouvé</p>
          <p className="text-[var(--text-muted)] text-sm mt-1">Essaie un autre terme de recherche</p>
          {search && (
            <button onClick={clearSearch} className="btn-primary mt-6">
              Voir tous les films
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
            onClick={() => setPage(p => p - 1)}
            className="btn-secondary px-4 py-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ← Précédent
          </button>
          <span className="text-sm text-[var(--text-muted)] px-4">
            {page} / {totalPages}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage(p => p + 1)}
            className="btn-secondary px-4 py-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Suivant →
          </button>
        </div>
      )}
    </div>
  )
}
