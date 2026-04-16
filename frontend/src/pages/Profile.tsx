import { useState, useEffect, useRef } from 'react'
import { Camera, Save, Eye, User, MapPin, Search, X, Award } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { usersApi, filmsApi, badgesApi } from '../services/api'
import type { Film, Badge, ReputationScore } from '../types'
import { BadgesGrid } from '../components/BadgeDisplay'

const MOOD_OPTIONS = [
  { value: 'rire', label: 'Envie de rire' },
  { value: 'reflechir', label: 'Besoin de réfléchir' },
  { value: 'emu', label: "Envie d'être ému" },
  { value: 'adrenaline', label: "Besoin d'adrénaline" },
]

const GENRE_OPTIONS = [
  'Action', 'Comédie', 'Drame', 'Thriller', 'Horreur',
  'Science-fiction', 'Animation', 'Documentaire', 'Romance', 'Aventure',
]

type Tab = 'infos' | 'preferences' | 'public' | 'badges'

export default function Profile() {
  const { user, fetchMe } = useAuthStore()
  const fileRef = useRef<HTMLInputElement>(null)
  const [tab, setTab] = useState<Tab>('infos')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState('')

  // Form state
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [city, setCity] = useState('')
  const [dateOfBirth, setDateOfBirth] = useState('')
  const [bio, setBio] = useState('')
  const [mood, setMood] = useState('')
  const [genrePrefs, setGenrePrefs] = useState<Record<string, number>>({})

  // Films signature
  const [filmsSignature, setFilmsSignature] = useState<Film[]>([])
  const [filmQuery, setFilmQuery] = useState('')
  const [filmResults, setFilmResults] = useState<Film[]>([])
  const [searchingFilms, setSearchingFilms] = useState(false)

  // Badges & réputation
  const [badges, setBadges] = useState<Badge[]>([])
  const [reputation, setReputation] = useState<ReputationScore | null>(null)

  useEffect(() => {
    if (user) {
      setFirstName(user.first_name)
      setLastName(user.last_name)
      setCity(user.city || '')
      setDateOfBirth(user.date_of_birth || '')
      setBio(user.profile?.bio || '')
      setMood(user.profile?.mood || '')
      setGenrePrefs(user.profile?.genre_preferences || {})
      setFilmsSignature(user.profile?.films_signature || [])
    }
  }, [user])

  // Fetch badges quand on ouvre l'onglet
  useEffect(() => {
    if (tab === 'badges' && user) {
      badgesApi.getMyBadges().then(res => setBadges(res.data.badges)).catch(() => {})
      badgesApi.getReputation(user.id).then(res => setReputation(res.data)).catch(() => {})
    }
  }, [tab, user])

  // Recherche TMDb debounced
  useEffect(() => {
    if (!filmQuery.trim()) { setFilmResults([]); return }
    const t = setTimeout(async () => {
      setSearchingFilms(true)
      try {
        const res = await filmsApi.tmdbSearch(filmQuery)
        setFilmResults(res.data)
      } finally {
        setSearchingFilms(false)
      }
    }, 400)
    return () => clearTimeout(t)
  }, [filmQuery])

  const showSuccess = (msg: string) => {
    setSuccess(msg)
    setTimeout(() => setSuccess(''), 3000)
  }

  const handleSaveInfos = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await usersApi.updateMe({ first_name: firstName, last_name: lastName, city, date_of_birth: dateOfBirth || null })
      await fetchMe()
      showSuccess('Informations mises à jour !')
    } finally {
      setLoading(false)
    }
  }

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await usersApi.updateProfile({
        bio, mood, genre_preferences: genrePrefs,
        films_signature_ids: filmsSignature.map(f => f.id),
      })
      await fetchMe()
      showSuccess('Profil mis à jour !')
    } finally {
      setLoading(false)
    }
  }

  const handlePictureChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true)
    try {
      await usersApi.uploadPicture(file)
      await fetchMe()
      showSuccess('Photo mise à jour !')
    } finally {
      setLoading(false)
    }
  }

  const toggleGenre = (genre: string) => {
    setGenrePrefs(prev => {
      if (prev[genre]) {
        const next = { ...prev }
        delete next[genre]
        return next
      }
      return { ...prev, [genre]: 7 }
    })
  }

  if (!user) return null

  return (
    <div className="min-h-screen max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-6 mb-8">
        {/* Avatar */}
        <div className="relative shrink-0">
          <div className="w-24 h-24 rounded-full overflow-hidden border-2"
            style={{ borderColor: 'var(--accent-red)' }}>
            {user.profile?.profile_picture ? (
              <img src={user.profile.profile_picture} alt="Avatar" className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-3xl font-bold"
                style={{ background: 'var(--bg-card)', color: 'var(--accent-red)' }}>
                {user.first_name?.[0]?.toUpperCase()}
              </div>
            )}
          </div>
          <button
            onClick={() => fileRef.current?.click()}
            className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-110"
            style={{ background: 'var(--accent-red)' }}
          >
            <Camera size={14} />
          </button>
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handlePictureChange} />
        </div>

        <div>
          <h1 className="text-2xl font-semibold text-white">{user.first_name} {user.last_name}</h1>
          <p className="text-[var(--text-muted)] text-sm">{user.email}</p>
          {user.city && <p className="text-[var(--text-muted)] text-sm flex items-center gap-1"><MapPin size={12} />{user.city}</p>}
        </div>
      </div>

      {/* Success message */}
      {success && (
        <div className="mb-6 px-4 py-3 rounded-lg text-sm text-green-400 flex items-center gap-2"
          style={{ background: 'rgba(74,222,128,0.1)', border: '1px solid rgba(74,222,128,0.2)' }}>
          <Save size={14} />
          {success}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 glass rounded-lg p-1 mb-6">
        {([
          { id: 'infos', label: 'Mes infos', icon: User },
          { id: 'preferences', label: 'Préférences', icon: Save },
          { id: 'public', label: 'Profil public', icon: Eye },
          { id: 'badges', label: 'Badges', icon: Award },
        ] as { id: Tab; label: string; icon: typeof User }[]).map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setTab(id)}
            className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === id ? 'bg-[var(--accent-red)] text-white' : 'text-[var(--text-muted)] hover:text-white'
            }`}>
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab: Mes infos */}
      {tab === 'infos' && (
        <form onSubmit={handleSaveInfos} className="glass rounded-2xl p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-1.5">Prénom</label>
              <input value={firstName} onChange={e => setFirstName(e.target.value)}
                className="input-field" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-1.5">Nom</label>
              <input value={lastName} onChange={e => setLastName(e.target.value)}
                className="input-field" required />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-1.5">Email</label>
            <input value={user.email} disabled className="input-field opacity-50 cursor-not-allowed" />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-1.5">Ville</label>
            <input value={city} onChange={e => setCity(e.target.value)}
              placeholder="Bruxelles" className="input-field" />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-1.5">Date de naissance</label>
            <input type="date" value={dateOfBirth} onChange={e => setDateOfBirth(e.target.value)}
              className="input-field" max={new Date().toISOString().split('T')[0]} />
          </div>
          <button type="submit" disabled={loading}
            className="btn-primary flex items-center gap-2 disabled:opacity-60">
            {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Save size={15} />}
            Enregistrer
          </button>
        </form>
      )}

      {/* Tab: Préférences */}
      {tab === 'preferences' && (
        <form onSubmit={handleSavePreferences} className="space-y-6">
          {/* Bio */}
          <div className="glass rounded-2xl p-6">
            <label className="block text-sm font-medium text-[var(--text-muted)] mb-1.5">Bio</label>
            <textarea
              value={bio}
              onChange={e => setBio(e.target.value)}
              rows={3}
              maxLength={500}
              placeholder="Parle un peu de toi et de tes films préférés..."
              className="input-field resize-none"
            />
            <p className="text-xs text-[var(--text-muted)] text-right mt-1">{bio.length}/500</p>
          </div>

          {/* Mood */}
          <div className="glass rounded-2xl p-6">
            <label className="block text-sm font-medium text-white mb-3">Humeur du moment</label>
            <div className="grid grid-cols-2 gap-2">
              {MOOD_OPTIONS.map(m => (
                <button
                  key={m.value}
                  type="button"
                  onClick={() => setMood(m.value)}
                  className={`px-4 py-3 rounded-lg text-sm text-left transition-all ${
                    mood === m.value
                      ? 'text-white border-[var(--accent-red)]'
                      : 'text-[var(--text-muted)] border-transparent hover:text-white'
                  }`}
                  style={{
                    background: mood === m.value ? 'rgba(230,57,70,0.15)' : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${mood === m.value ? 'rgba(230,57,70,0.4)' : 'rgba(255,255,255,0.05)'}`,
                  }}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          {/* Genres */}
          <div className="glass rounded-2xl p-6">
            <label className="block text-sm font-medium text-white mb-3">
              Genres préférés
              <span className="text-[var(--text-muted)] font-normal ml-2 text-xs">
                ({Object.keys(genrePrefs).length} sélectionné{Object.keys(genrePrefs).length > 1 ? 's' : ''})
              </span>
            </label>
            <div className="flex flex-wrap gap-2">
              {GENRE_OPTIONS.map(genre => {
                const selected = !!genrePrefs[genre]
                return (
                  <button
                    key={genre}
                    type="button"
                    onClick={() => toggleGenre(genre)}
                    className={`px-3 py-1.5 rounded-full text-sm transition-all ${
                      selected ? 'text-white' : 'text-[var(--text-muted)] hover:text-white'
                    }`}
                    style={{
                      background: selected ? 'var(--accent-red)' : 'rgba(255,255,255,0.05)',
                      border: `1px solid ${selected ? 'transparent' : 'rgba(255,255,255,0.08)'}`,
                    }}
                  >
                    {genre}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Films signature */}
          <div className="glass rounded-2xl p-6">
            <label className="block text-sm font-medium text-white mb-1">
              Films signature
              <span className="text-[var(--text-muted)] font-normal ml-2 text-xs">
                ({filmsSignature.length}/5) — utilisés pour le matching
              </span>
            </label>
            <p className="text-xs text-[var(--text-muted)] mb-3">Tes films préférés de tous les temps, pas forcément au cinéma.</p>
            {filmsSignature.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {filmsSignature.map(f => (
                  <span key={f.id} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm text-white"
                    style={{ background: 'var(--accent-red)', border: '1px solid transparent' }}>
                    {f.title}
                    <button type="button" onClick={() => setFilmsSignature(prev => prev.filter(x => x.id !== f.id))}>
                      <X size={12} />
                    </button>
                  </span>
                ))}
              </div>
            )}
            {filmsSignature.length < 5 && (
              <div className="relative">
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
                  <input type="text" value={filmQuery} onChange={e => setFilmQuery(e.target.value)}
                    placeholder="Rechercher un film (ex: Interstellar)..." className="input-field pl-9" />
                  {searchingFilms && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  )}
                </div>
                {filmResults.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 rounded-xl overflow-hidden shadow-xl"
                    style={{ background: 'var(--bg-card)', border: '1px solid rgba(255,255,255,0.08)' }}>
                    {filmResults.map(f => (
                      <button key={f.id} type="button"
                        onClick={() => {
                          if (!filmsSignature.find(x => x.id === f.id))
                            setFilmsSignature(prev => [...prev, f])
                          setFilmQuery(''); setFilmResults([])
                        }}
                        className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-white/5 transition-colors text-left">
                        {f.poster_url
                          ? <img src={f.poster_url} alt={f.title} className="w-8 h-12 object-cover rounded" />
                          : <div className="w-8 h-12 rounded flex items-center justify-center text-xs text-[var(--text-muted)]"
                              style={{ background: 'rgba(255,255,255,0.05)' }}>?</div>
                        }
                        <span className="text-sm text-white">{f.title}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <button type="submit" disabled={loading}
            className="btn-primary flex items-center gap-2 disabled:opacity-60">
            {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Save size={15} />}
            Enregistrer les préférences
          </button>
        </form>
      )}

      {/* Tab: Profil public */}
      {tab === 'public' && (
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-full overflow-hidden border-2"
              style={{ borderColor: 'var(--accent-red)' }}>
              {user.profile?.profile_picture ? (
                <img src={user.profile.profile_picture} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-2xl font-bold"
                  style={{ background: 'var(--bg-card)', color: 'var(--accent-red)' }}>
                  {user.first_name?.[0]?.toUpperCase()}
                </div>
              )}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">{user.first_name}, {
                user.date_of_birth
                  ? Math.floor((Date.now() - new Date(user.date_of_birth).getTime()) / (365.25 * 24 * 3600 * 1000))
                  : '??'
              } ans</h3>
              {user.city && <p className="text-[var(--text-muted)] text-sm flex items-center gap-1"><MapPin size={12} />{user.city}</p>}
              {user.profile?.mood && (
                <p className="text-sm mt-0.5" style={{ color: 'var(--accent-gold)' }}>
                  {MOOD_OPTIONS.find(m => m.value === user.profile.mood)?.label}
                </p>
              )}
            </div>
          </div>

          {user.profile?.bio && (
            <p className="text-[var(--text-muted)] text-sm mb-4 leading-relaxed">{user.profile.bio}</p>
          )}

          {Object.keys(genrePrefs).length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">Genres préférés</p>
              <div className="flex flex-wrap gap-2">
                {Object.keys(user.profile?.genre_preferences || {}).map(g => (
                  <span key={g} className="px-3 py-1 rounded-full text-xs"
                    style={{ background: 'rgba(230,57,70,0.15)', color: 'var(--accent-red)', border: '1px solid rgba(230,57,70,0.3)' }}>
                    {g}
                  </span>
                ))}
              </div>
            </div>
          )}

          <p className="text-xs text-[var(--text-muted)] italic">
            C'est ainsi que les autres utilisateurs voient ton profil. Email et mot de passe ne sont jamais affichés.
          </p>
        </div>
      )}

      {/* Tab: Badges */}
      {tab === 'badges' && (
        <div className="space-y-6">
          {/* Score de réputation */}
          {reputation && (
            <div className="glass rounded-2xl p-6">
              <h3 className="text-sm font-medium text-white mb-4 uppercase tracking-wider">Score de réputation</h3>
              {reputation.count >= 3 ? (
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <p className="text-4xl font-bold" style={{ color: 'var(--accent-gold)' }}>
                      {reputation.score}
                    </p>
                    <p className="text-xs text-[var(--text-muted)] mt-1">/ 5</p>
                  </div>
                  <div>
                    <p className="text-white font-semibold">{reputation.label}</p>
                    <p className="text-xs text-[var(--text-muted)]">{reputation.count} avis reçus</p>
                    {reputation.would_go_again_pct !== null && (
                      <p className="text-xs mt-1" style={{ color: 'var(--accent-gold)' }}>
                        {reputation.would_go_again_pct}% repartiraient avec toi
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <span className="text-2xl font-bold text-[var(--text-muted)]">Nouveau</span>
                  <p className="text-xs text-[var(--text-muted)]">
                    {reputation.count > 0
                      ? `${reputation.count} avis — encore ${3 - reputation.count} pour afficher ton score`
                      : 'Aucun avis reçu pour l\'instant'}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Grille de badges */}
          <div className="glass rounded-2xl p-6">
            <h3 className="text-sm font-medium text-white mb-6 uppercase tracking-wider">Mes badges</h3>
            <BadgesGrid badges={badges} />
          </div>
        </div>
      )}
    </div>
  )
}
