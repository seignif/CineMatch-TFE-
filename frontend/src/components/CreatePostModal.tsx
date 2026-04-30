import React, { useState } from 'react'
import { X } from 'lucide-react'
import type { Film, Post } from '../types'
import { socialApi, filmsApi } from '../services/api'

interface Props {
  initialFilm?: Film | null
  onClose: () => void
  onCreated: (post: Post) => void
}

export const CreatePostModal: React.FC<Props> = ({ initialFilm, onClose, onCreated }) => {
  const [content, setContent] = useState('')
  const [selectedFilm, setSelectedFilm] = useState<Film | null>(initialFilm ?? null)
  const [filmSearch, setFilmSearch] = useState('')
  const [filmResults, setFilmResults] = useState<Film[]>([])
  const [loading, setLoading] = useState(false)

  const handleFilmSearch = async (q: string) => {
    setFilmSearch(q)
    if (q.length < 2) { setFilmResults([]); return }
    try {
      const res = await filmsApi.getAll({ search: q })
      const results = res.data.results ?? res.data
      setFilmResults(results.slice(0, 5))
    } catch {}
  }

  const handleSubmit = async () => {
    if (!content.trim()) return
    setLoading(true)
    try {
      const res = await socialApi.createPost({
        content: content.trim(),
        film_id: selectedFilm?.id,
      })
      onCreated(res.data)
      onClose()
    } catch {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-end sm:items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-[var(--bg-card)] rounded-2xl w-full max-w-lg border border-white/10"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <h3 className="text-white font-semibold">Nouveau post</h3>
          <button onClick={onClose} className="text-[var(--text-muted)] hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Textarea */}
          <div>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder="Partagez votre avis sur un film, une sortie, une découverte..."
              maxLength={280}
              rows={4}
              autoFocus
              className="w-full bg-black/30 border border-white/10 rounded-xl p-3 text-white text-sm placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-red)] resize-none"
            />
            <p className={`text-right text-xs mt-1 ${content.length > 250 ? 'text-[var(--accent-red)]' : 'text-[var(--text-muted)]'}`}>
              {content.length}/280
            </p>
          </div>

          {/* Film sélectionné */}
          {selectedFilm ? (
            <div className="flex items-center gap-3 bg-black/30 rounded-xl p-3">
              {selectedFilm.poster_url && (
                <img src={selectedFilm.poster_url} alt="" className="w-8 h-11 object-cover rounded" />
              )}
              <span className="text-white text-sm flex-1 truncate">{selectedFilm.title}</span>
              <button
                onClick={() => setSelectedFilm(null)}
                className="text-[var(--text-muted)] hover:text-white transition-colors"
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <div className="relative">
              <input
                type="text"
                value={filmSearch}
                onChange={e => handleFilmSearch(e.target.value)}
                placeholder="Lier un film (optionnel)..."
                className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-red)]"
              />
              {filmResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-[var(--bg-card)] border border-white/10 rounded-xl overflow-hidden z-10 shadow-xl">
                  {filmResults.map(film => (
                    <div
                      key={film.id}
                      className="flex items-center gap-3 px-4 py-2.5 hover:bg-white/5 cursor-pointer transition-colors"
                      onClick={() => { setSelectedFilm(film); setFilmSearch(''); setFilmResults([]) }}
                    >
                      {film.poster_url && (
                        <img src={film.poster_url} alt="" className="w-7 h-10 object-cover rounded" />
                      )}
                      <span className="text-white text-sm truncate">{film.title}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-white/10">
          <button
            onClick={onClose}
            className="px-4 py-2 text-[var(--text-muted)] hover:text-white text-sm transition-colors"
          >
            Annuler
          </button>
          <button
            onClick={handleSubmit}
            disabled={!content.trim() || loading}
            className="px-5 py-2 bg-[var(--accent-red)] text-white rounded-xl text-sm font-medium disabled:opacity-40 hover:bg-[var(--accent-red)]/80 transition-colors"
          >
            {loading ? 'Publication...' : 'Publier'}
          </button>
        </div>
      </div>
    </div>
  )
}
