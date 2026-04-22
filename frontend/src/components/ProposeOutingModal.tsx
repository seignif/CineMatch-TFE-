import { useState, useEffect } from 'react'
import { X, Search, ChevronRight, Film, MapPin, Clock, MessageSquare } from 'lucide-react'
import { filmsApi, outingsApi } from '../services/api'
import type { Film as FilmType, Seance } from '../types'

interface Props {
  matchId: number
  partnerName: string
  onClose: () => void
  onSuccess: () => void
}

type Mode = 'seance' | 'libre'

function formatShowtime(iso: string) {
  return new Date(iso).toLocaleString('fr-BE', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function ProposeOutingModal({ matchId, partnerName, onClose, onSuccess }: Props) {
  const [mode, setMode] = useState<Mode>('seance')
  const [query, setQuery] = useState('')
  const [films, setFilms] = useState<FilmType[]>([])
  const [selectedFilm, setSelectedFilm] = useState<FilmType | null>(null)
  const [seances, setSeances] = useState<Seance[]>([])
  const [selectedSeance, setSelectedSeance] = useState<Seance | null>(null)
  const [meetingPlace, setMeetingPlace] = useState('')
  const [meetingTime, setMeetingTime] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [loadingFilms, setLoadingFilms] = useState(false)
  const [loadingSeances, setLoadingSeances] = useState(false)

  // Debounced film search
  useEffect(() => {
    if (!query.trim()) {
      setFilms([])
      return
    }
    const t = setTimeout(() => {
      setLoadingFilms(true)
      filmsApi
        .getAll({ search: query })
        .then(res => setFilms(res.data.results ?? res.data))
        .catch(() => setFilms([]))
        .finally(() => setLoadingFilms(false))
    }, 400)
    return () => clearTimeout(t)
  }, [query])

  // Load seances when film is selected
  useEffect(() => {
    if (!selectedFilm) {
      setSeances([])
      setSelectedSeance(null)
      return
    }
    setLoadingSeances(true)
    filmsApi
      .getSeances(selectedFilm.id)
      .then(res => setSeances(res.data))
      .catch(() => setSeances([]))
      .finally(() => setLoadingSeances(false))
  }, [selectedFilm])

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      await outingsApi.create({
        match: matchId,
        seance_id: mode === 'seance' ? (selectedSeance?.id ?? null) : null,
        meeting_place: mode === 'libre' ? meetingPlace : '',
        meeting_time: mode === 'libre' && meetingTime ? meetingTime : undefined,
        proposal_message: message,
      })
      onSuccess()
    } catch {
      // ignore
    } finally {
      setSubmitting(false)
    }
  }

  const canSubmit = mode === 'seance' ? selectedSeance !== null : true

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="glass rounded-2xl w-full max-w-lg max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/10">
          <div>
            <h2 className="text-white font-semibold text-lg">Proposer une sortie</h2>
            <p className="text-[var(--text-muted)] text-sm">avec {partnerName}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/5 text-[var(--text-muted)] transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1 p-5 space-y-5">
          {/* Mode toggle */}
          <div className="flex gap-2">
            {(['seance', 'libre'] as const).map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 py-2 rounded-xl text-sm font-medium transition-colors ${
                  mode === m
                    ? 'bg-[var(--accent-red)] text-white'
                    : 'glass text-[var(--text-muted)] hover:text-white'
                }`}
              >
                {m === 'seance' ? 'Choisir une séance' : 'Lieu libre'}
              </button>
            ))}
          </div>

          {/* Séance picker */}
          {mode === 'seance' && (
            <>
              {!selectedFilm ? (
                <div>
                  <label className="text-xs text-[var(--text-muted)] mb-1.5 block">
                    Rechercher un film
                  </label>
                  <div className="relative">
                    <Search
                      size={14}
                      className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
                    />
                    <input
                      value={query}
                      onChange={e => setQuery(e.target.value)}
                      placeholder="Titre du film..."
                      className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-red)]"
                    />
                  </div>
                  {loadingFilms && (
                    <p className="text-xs text-[var(--text-muted)] mt-2">Recherche...</p>
                  )}
                  {films.length > 0 && (
                    <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
                      {films.map(f => (
                        <button
                          key={f.id}
                          onClick={() => {
                            setSelectedFilm(f)
                            setQuery('')
                            setFilms([])
                          }}
                          className="w-full flex items-center gap-3 p-2 rounded-xl hover:bg-white/5 transition-colors text-left"
                        >
                          {f.poster_url ? (
                            <img
                              src={f.poster_url}
                              alt=""
                              className="w-8 h-12 object-cover rounded shrink-0"
                            />
                          ) : (
                            <div className="w-8 h-12 bg-white/10 rounded flex items-center justify-center shrink-0">
                              <Film size={14} className="text-[var(--text-muted)]" />
                            </div>
                          )}
                          <span className="text-sm text-white flex-1">{f.title}</span>
                          <ChevronRight size={14} className="text-[var(--text-muted)]" />
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <p className="text-sm text-white font-medium flex-1">{selectedFilm.title}</p>
                    <button
                      onClick={() => {
                        setSelectedFilm(null)
                        setSelectedSeance(null)
                        setSeances([])
                      }}
                      className="text-xs text-[var(--accent-red)] hover:underline"
                    >
                      Changer
                    </button>
                  </div>
                  <label className="text-xs text-[var(--text-muted)] mb-1.5 block">
                    Choisir une séance
                  </label>
                  {loadingSeances && (
                    <p className="text-xs text-[var(--text-muted)]">Chargement des séances...</p>
                  )}
                  {!loadingSeances && seances.length === 0 && (
                    <p className="text-xs text-[var(--text-muted)]">
                      Aucune séance disponible pour ce film.
                    </p>
                  )}
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {seances.map(s => (
                      <button
                        key={s.id}
                        onClick={() => !s.is_sold_out && setSelectedSeance(s)}
                        disabled={s.is_sold_out}
                        className={`w-full flex flex-col gap-0.5 p-3 rounded-xl border transition-colors text-left ${
                          selectedSeance?.id === s.id
                            ? 'border-[var(--accent-red)] bg-[var(--accent-red)]/10'
                            : 'border-white/10 bg-white/3 hover:border-white/20'
                        } ${s.is_sold_out ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}
                      >
                        <div className="flex items-center gap-1.5 text-sm text-white">
                          <Clock size={12} />
                          {formatShowtime(s.showtime)}
                        </div>
                        <div className="text-xs text-[var(--text-muted)]">
                          {s.language}
                          {s.hall ? ` · Salle ${s.hall}` : ''}
                        </div>
                        {s.is_sold_out && <span className="text-xs text-red-400">Complet</span>}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Lieu libre */}
          {mode === 'libre' && (
            <div className="space-y-4">
              <div>
                <label className="text-xs text-[var(--text-muted)] mb-1.5 block">
                  Lieu de rendez-vous
                </label>
                <div className="relative">
                  <MapPin
                    size={14}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
                  />
                  <input
                    value={meetingPlace}
                    onChange={e => setMeetingPlace(e.target.value)}
                    placeholder="Ex: Hall du Kinepolis Braine..."
                    className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-red)]"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-[var(--text-muted)] mb-1.5 block">
                  Date et heure
                </label>
                <div className="relative">
                  <Clock
                    size={14}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
                  />
                  <input
                    type="datetime-local"
                    value={meetingTime}
                    onChange={e => setMeetingTime(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-[var(--accent-red)]"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Message */}
          <div>
            <label className="text-xs text-[var(--text-muted)] mb-1.5 block">
              Message (facultatif)
            </label>
            <div className="relative">
              <MessageSquare
                size={14}
                className="absolute left-3 top-3 text-[var(--text-muted)]"
              />
              <textarea
                value={message}
                onChange={e => setMessage(e.target.value)}
                rows={3}
                placeholder="Ajouter un message pour votre match..."
                className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-red)] resize-none"
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-5 border-t border-white/10 flex gap-3">
          <button onClick={onClose} className="flex-1 btn-secondary py-2.5 text-sm">
            Annuler
          </button>
          <button
            onClick={handleSubmit}
            disabled={!canSubmit || submitting}
            className="flex-1 btn-primary py-2.5 text-sm disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {submitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Envoi...
              </>
            ) : (
              'Proposer la sortie'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
