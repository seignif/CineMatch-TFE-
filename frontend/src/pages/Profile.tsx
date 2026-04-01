import { useState, useEffect, useRef } from 'react'
import { Camera, Save, Eye, User, MapPin } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { usersApi } from '../services/api'

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

type Tab = 'infos' | 'preferences' | 'public'

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
  const [bio, setBio] = useState('')
  const [mood, setMood] = useState('')
  const [genrePrefs, setGenrePrefs] = useState<Record<string, number>>({})

  useEffect(() => {
    if (user) {
      setFirstName(user.first_name)
      setLastName(user.last_name)
      setCity(user.city || '')
      setBio(user.profile?.bio || '')
      setMood(user.profile?.mood || '')
      setGenrePrefs(user.profile?.genre_preferences || {})
    }
  }, [user])

  const showSuccess = (msg: string) => {
    setSuccess(msg)
    setTimeout(() => setSuccess(''), 3000)
  }

  const handleSaveInfos = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await usersApi.updateMe({ first_name: firstName, last_name: lastName, city })
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
      await usersApi.updateProfile({ bio, mood, genre_preferences: genrePrefs })
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
        ] as { id: Tab; label: string; icon: typeof User }[]).map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setTab(id)}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
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
    </div>
  )
}
