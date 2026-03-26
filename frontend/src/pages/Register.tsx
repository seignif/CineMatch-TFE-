import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Check, X } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

function PasswordStrength({ password }: { password: string }) {
  const checks = [
    { label: '8 caractères minimum', ok: password.length >= 8 },
    { label: 'Une majuscule', ok: /[A-Z]/.test(password) },
    { label: 'Un chiffre', ok: /[0-9]/.test(password) },
  ]
  if (!password) return null
  return (
    <div className="mt-2 space-y-1">
      {checks.map(c => (
        <div key={c.label} className="flex items-center gap-2 text-xs">
          {c.ok ? <Check size={12} className="text-green-400" /> : <X size={12} className="text-[var(--text-muted)]" />}
          <span className={c.ok ? 'text-green-400' : 'text-[var(--text-muted)]'}>{c.label}</span>
        </div>
      ))}
    </div>
  )
}

export default function Register() {
  const navigate = useNavigate()
  const { register } = useAuthStore()
  const [form, setForm] = useState({
    email: '', username: '', first_name: '', last_name: '',
    city: '', password: '', password2: '',
  })
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const set = (field: string, value: string) => {
    setForm(f => ({ ...f, [field]: value }))
    setErrors(e => ({ ...e, [field]: '' }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    if (form.password !== form.password2) {
      setErrors({ password2: 'Les mots de passe ne correspondent pas.' })
      return
    }

    setLoading(true)
    try {
      await register(form)
      navigate('/films')
    } catch (err: unknown) {
      const data = (err as { response?: { data?: Record<string, string[]> } })?.response?.data
      if (data) {
        const mapped: Record<string, string> = {}
        Object.entries(data).forEach(([k, v]) => {
          mapped[k] = Array.isArray(v) ? v[0] : String(v)
        })
        setErrors(mapped)
      } else {
        setErrors({ general: 'Une erreur est survenue. Réessaie.' })
      }
    } finally {
      setLoading(false)
    }
  }

  const fields = [
    { id: 'email', label: 'Email', type: 'email', placeholder: 'toi@exemple.com', required: true },
    { id: 'username', label: "Nom d'utilisateur", type: 'text', placeholder: 'cinephile42', required: true },
    { id: 'first_name', label: 'Prénom', type: 'text', placeholder: 'Alex', required: true },
    { id: 'last_name', label: 'Nom', type: 'text', placeholder: 'Dupont', required: true },
    { id: 'city', label: 'Ville', type: 'text', placeholder: 'Bruxelles', required: false },
  ]

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12"
      style={{ background: 'var(--bg-secondary)' }}>
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <Link to="/" className="font-display text-4xl tracking-wider">
            CINE<span style={{ color: 'var(--accent-red)' }}>MATCH</span>
          </Link>
          <h2 className="text-xl font-semibold text-white mt-4 mb-1">Crée ton compte</h2>
          <p className="text-[var(--text-muted)] text-sm">Rejoins la communauté des cinéphiles belges</p>
        </div>

        <div className="glass rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {fields.slice(2, 4).map(f => (
                <div key={f.id}>
                  <label className="block text-sm font-medium text-[var(--text-muted)] mb-1.5">
                    {f.label}{f.required && <span className="text-[var(--accent-red)] ml-0.5">*</span>}
                  </label>
                  <input
                    type={f.type}
                    value={form[f.id as keyof typeof form]}
                    onChange={e => set(f.id, e.target.value)}
                    placeholder={f.placeholder}
                    required={f.required}
                    className="input-field"
                  />
                  {errors[f.id] && <p className="text-xs text-[var(--accent-red)] mt-1">{errors[f.id]}</p>}
                </div>
              ))}
            </div>

            {[fields[0], fields[1], fields[4]].map(f => (
              <div key={f.id}>
                <label className="block text-sm font-medium text-[var(--text-muted)] mb-1.5">
                  {f.label}{f.required && <span className="text-[var(--accent-red)] ml-0.5">*</span>}
                </label>
                <input
                  type={f.type}
                  value={form[f.id as keyof typeof form]}
                  onChange={e => set(f.id, e.target.value)}
                  placeholder={f.placeholder}
                  required={f.required}
                  className="input-field"
                />
                {errors[f.id] && <p className="text-xs text-[var(--accent-red)] mt-1">{errors[f.id]}</p>}
              </div>
            ))}

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-1.5">
                Mot de passe<span className="text-[var(--accent-red)] ml-0.5">*</span>
              </label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={form.password}
                  onChange={e => set('password', e.target.value)}
                  placeholder="••••••••"
                  required
                  className="input-field pr-10"
                />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-white">
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <PasswordStrength password={form.password} />
              {errors.password && <p className="text-xs text-[var(--accent-red)] mt-1">{errors.password}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-1.5">
                Confirmer le mot de passe<span className="text-[var(--accent-red)] ml-0.5">*</span>
              </label>
              <input
                type="password"
                value={form.password2}
                onChange={e => set('password2', e.target.value)}
                placeholder="••••••••"
                required
                className="input-field"
              />
              {errors.password2 && <p className="text-xs text-[var(--accent-red)] mt-1">{errors.password2}</p>}
            </div>

            {errors.general && (
              <div className="px-4 py-3 rounded-lg text-sm text-[var(--accent-red)]"
                style={{ background: 'rgba(230,57,70,0.1)', border: '1px solid rgba(230,57,70,0.2)' }}>
                {errors.general}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 mt-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : 'Créer mon compte'}
            </button>
          </form>

          <p className="text-center text-sm text-[var(--text-muted)] mt-6">
            Déjà un compte ?{' '}
            <Link to="/login" className="font-medium hover:underline" style={{ color: 'var(--accent-red)' }}>
              Se connecter
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
