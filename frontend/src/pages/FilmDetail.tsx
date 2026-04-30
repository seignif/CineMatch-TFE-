import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Clock, Star, Play, Calendar, X, Eye } from 'lucide-react'
import { filmsApi, watchedApi, socialApi } from '../services/api'
import { useAuthStore } from '../store/authStore'
import SeanceCard from '../components/SeanceCard'
import { PostCard } from '../components/PostCard'
import { CreatePostModal } from '../components/CreatePostModal'
import type { Film, Seance, PublicReview, WatchedFilm, Post } from '../types'

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
  const { user } = useAuthStore()
  const [film, setFilm] = useState<Film | null>(null)
  const [seances, setSeances] = useState<Seance[]>([])
  const [loading, setLoading] = useState(true)
  const [showTrailer, setShowTrailer] = useState(false)
  const [selectedCinema, setSelectedCinema] = useState<string>('all')
  const [langFilter, setLangFilter] = useState<string>('')

  // Journal (US-063)
  const [showWatchedModal, setShowWatchedModal] = useState(false)
  const [myEntry, setMyEntry] = useState<WatchedFilm | null>(null)
  const [watchRating, setWatchRating] = useState(0)
  const [watchReview, setWatchReview] = useState('')
  const [watchDate, setWatchDate] = useState('')
  const [watchPublic, setWatchPublic] = useState(true)
  const [savingWatch, setSavingWatch] = useState(false)

  // Forum (US-064)
  const [communityReviews, setCommunityReviews] = useState<PublicReview[]>([])

  // L'Entracte (US-071)
  const [showCreatePost, setShowCreatePost] = useState(false)
  const [filmPosts, setFilmPosts] = useState<Post[]>([])

  useEffect(() => {
    if (!id) return
    const filmId = parseInt(id)
    const defaultLang = user?.profile?.language_preference
    if (defaultLang && defaultLang !== 'both') setLangFilter(defaultLang)

    Promise.all([
      filmsApi.getById(filmId),
      filmsApi.getSeances(filmId),
      filmsApi.getReviews(filmId),
    ]).then(([filmRes, seancesRes, reviewsRes]) => {
      setFilm(filmRes.data)
      setSeances(seancesRes.data)
      setCommunityReviews(reviewsRes.data.results ?? reviewsRes.data)
    }).catch(() => navigate('/films'))
      .finally(() => setLoading(false))

    // Posts L'Entracte sur ce film
    socialApi.getPosts({ film_id: filmId }).then(res => {
      const data = res.data
      setFilmPosts((data.results ?? data).slice(0, 3))
    }).catch(() => {})

    // Mon entrée journal
    watchedApi.getAll().then(res => {
      const all: WatchedFilm[] = res.data.results ?? res.data
      const mine = all.find(e => e.film_info?.id === filmId)
      if (mine) setMyEntry(mine)
    }).catch(() => {})
  }, [id, navigate, user])

  const handleSaveWatch = async () => {
    if (!film || !watchRating) return
    setSavingWatch(true)
    try {
      if (myEntry) {
        const res = await watchedApi.update(myEntry.id, {
          rating: watchRating, review: watchReview,
          watched_date: watchDate || null, is_public: watchPublic,
        })
        setMyEntry(res.data)
      } else {
        const res = await watchedApi.create({
          film_id: film.id, rating: watchRating, review: watchReview,
          watched_date: watchDate || null, is_public: watchPublic,
        })
        setMyEntry(res.data)
      }
      // Rafraîchir les avis publics
      const reviewsRes = await filmsApi.getReviews(film.id)
      setCommunityReviews(reviewsRes.data.results ?? reviewsRes.data)
      setShowWatchedModal(false)
    } finally {
      setSavingWatch(false)
    }
  }

  const openWatchModal = () => {
    if (myEntry) {
      setWatchRating(myEntry.rating ?? 0)
      setWatchReview(myEntry.review)
      setWatchDate(myEntry.watched_date ?? '')
      setWatchPublic(myEntry.is_public)
    }
    setShowWatchedModal(true)
  }

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

  const langFilteredSeances = langFilter === 'vf'
    ? seances.filter(s => ['FR', 'NL'].includes(s.language))
    : langFilter === 'vo'
      ? seances.filter(s => !['FR', 'NL'].includes(s.language))
      : seances

  const filteredSeances = selectedCinema === 'all'
    ? langFilteredSeances
    : langFilteredSeances.filter(s => s.cinema.name === selectedCinema)

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

              <div className="flex flex-wrap gap-3 mt-4">
                {film.trailer_youtube_key && (
                  <button onClick={() => setShowTrailer(true)} className="flex items-center gap-2 btn-primary">
                    <Play size={16} fill="white" />
                    Bande-annonce
                  </button>
                )}
                {user && (
                  <button onClick={openWatchModal}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors btn-secondary">
                    <Eye size={15} />
                    {myEntry ? 'Modifier mon avis' : "J'ai vu ce film"}
                  </button>
                )}
                {user && (
                  <button
                    onClick={() => setShowCreatePost(true)}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors bg-white/10 hover:bg-white/15 text-white"
                  >
                    Partager dans L'Entracte
                  </button>
                )}
              </div>
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
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
            <h2 className="font-display text-2xl tracking-wider text-white">
              SÉANCES DISPONIBLES
              <span className="text-[var(--text-muted)] text-lg ml-3 font-sans font-normal normal-case">
                ({seances.length} séance{seances.length !== 1 ? 's' : ''})
              </span>
            </h2>

            {cinemas.length > 1 && (
              <select value={selectedCinema} onChange={e => setSelectedCinema(e.target.value)}
                className="input-field w-auto text-sm">
                <option value="all">Tous les cinémas</option>
                {cinemas.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            )}
          </div>

          {/* Filtre VF/VO */}
          <div className="flex gap-2 mb-6">
            {[
              { value: '', label: 'Toutes' },
              { value: 'vf', label: 'VF' },
              { value: 'vo', label: 'VO/VOST' },
            ].map(opt => (
              <button key={opt.value} onClick={() => setLangFilter(opt.value)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                  langFilter === opt.value
                    ? 'bg-[var(--accent-red)] text-white'
                    : 'glass text-[var(--text-muted)] hover:text-white'
                }`}>
                {opt.label}
              </button>
            ))}
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

      {/* Section forum (US-064) */}
      <div className="max-w-7xl mx-auto px-4 pb-12">
        <h2 className="font-display text-2xl tracking-wider text-white mb-6">
          AVIS DE LA COMMUNAUTE
        </h2>
        {communityReviews.length === 0 ? (
          <div className="glass rounded-xl p-8 text-center">
            <p className="text-[var(--text-muted)] mb-4">Soyez le premier à donner votre avis !</p>
            {user && (
              <button onClick={openWatchModal} className="btn-primary">
                Donner mon avis
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {communityReviews.map(review => (
              <div key={review.id} className="glass rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm"
                      style={{ background: 'var(--accent-red)', color: 'white' }}>
                      {review.author_name[0]?.toUpperCase()}
                    </div>
                    <div>
                      <span className="text-white text-sm font-medium">{review.author_name}</span>
                      <div className="flex gap-0.5">
                        {[1,2,3,4,5].map(n => (
                          <span key={n} style={{ color: n <= review.rating ? 'var(--accent-gold)' : 'rgba(255,255,255,0.2)', fontSize: '12px' }}>★</span>
                        ))}
                      </div>
                    </div>
                  </div>
                  {review.watched_date && (
                    <span className="text-xs text-[var(--text-muted)]">
                      {new Date(review.watched_date).toLocaleDateString('fr-BE')}
                    </span>
                  )}
                </div>
                {review.review && (
                  <p className="text-sm text-[var(--text-muted)] italic">"{review.review}"</p>
                )}
              </div>
            ))}
            {user && (
              <button onClick={openWatchModal}
                className="text-sm text-[var(--text-muted)] hover:text-white transition-colors underline">
                {myEntry ? 'Modifier mon avis' : 'Donner mon avis'}
              </button>
            )}
          </div>
        )}
      </div>

      {/* L'Entracte — posts sur ce film (US-071) */}
      {filmPosts.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-semibold">Dans L'Entracte</h3>
            <button
              onClick={() => navigate(`/entracte?film_id=${film.id}`)}
              className="text-[var(--accent-red)] text-sm hover:underline"
            >
              Voir tous
            </button>
          </div>
          <div className="space-y-3">
            {filmPosts.map(post => (
              <PostCard
                key={post.id}
                post={post}
                onDelete={id => setFilmPosts(prev => prev.filter(p => p.id !== id))}
              />
            ))}
          </div>
        </div>
      )}

      {/* CreatePostModal (US-071) */}
      {showCreatePost && (
        <CreatePostModal
          initialFilm={film}
          onClose={() => setShowCreatePost(false)}
          onCreated={post => {
            setFilmPosts(prev => [post, ...prev].slice(0, 3))
            setShowCreatePost(false)
          }}
        />
      )}

      {/* Modal "J'ai vu ce film" (US-063) */}
      {showWatchedModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.8)' }}
          onClick={() => setShowWatchedModal(false)}>
          <div className="glass rounded-2xl p-6 w-full max-w-md space-y-4"
            onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="text-white font-semibold">Mon avis — {film.title}</h3>
              <button onClick={() => setShowWatchedModal(false)} className="text-[var(--text-muted)] hover:text-white">
                <X size={18} />
              </button>
            </div>

            <div>
              <label className="block text-xs text-[var(--text-muted)] mb-2">Ma note</label>
              <div className="flex gap-2">
                {[1,2,3,4,5].map(n => (
                  <button key={n} type="button" onClick={() => setWatchRating(n)}
                    style={{ fontSize: '28px', color: n <= watchRating ? 'var(--accent-gold)' : 'rgba(255,255,255,0.2)' }}>
                    ★
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs text-[var(--text-muted)] mb-1">Date de visionnage</label>
              <input type="date" value={watchDate} onChange={e => setWatchDate(e.target.value)}
                className="input-field text-sm" max={new Date().toISOString().split('T')[0]} />
            </div>

            <div>
              <label className="block text-xs text-[var(--text-muted)] mb-1">Commentaire (optionnel)</label>
              <textarea value={watchReview} onChange={e => setWatchReview(e.target.value)}
                rows={3} placeholder="Mon avis sur ce film..." className="input-field resize-none text-sm" />
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={watchPublic} onChange={e => setWatchPublic(e.target.checked)}
                className="w-4 h-4 accent-[var(--accent-red)]" />
              <span className="text-sm text-[var(--text-muted)]">Rendre mon avis public</span>
            </label>

            <button onClick={handleSaveWatch} disabled={savingWatch || !watchRating}
              className="btn-primary w-full disabled:opacity-60 flex items-center justify-center gap-2">
              {savingWatch && <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
              {myEntry ? 'Mettre à jour' : 'Enregistrer'}
            </button>
          </div>
        </div>
      )}

      {/* Trailer modal */}
      {showTrailer && film.trailer_youtube_key && (
        <TrailerModal youtubeKey={film.trailer_youtube_key} onClose={() => setShowTrailer(false)} />
      )}
    </div>
  )
}
