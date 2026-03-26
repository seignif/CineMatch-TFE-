import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Film } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/films')
    } catch {
      setError('Email ou mot de passe incorrect.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left — poster */}
      <div className="hidden lg:flex flex-1 relative items-center justify-center overflow-hidden"
        style={{ background: 'linear-gradient(135deg, #0A0A0F 0%, #1A1A2E 50%, #0F3460 100%)' }}>
        <div className="absolute inset-0 opacity-20"
          style={{ backgroundImage: 'radial-gradient(circle at 30% 50%, #E63946 0%, transparent 60%)' }} />
        <div className="relative text-center z-10 p-12">
          <Film size={60} className="mx-auto mb-6" style={{ color: 'var(--accent-red)' }} />
          <h1 className="font-display text-7xl tracking-wider text-white">CINE<span style={{ color: 'var(--accent-red)' }}>MATCH</span></h1>
          <p className="text-[var(--text-muted)] mt-4 text-lg max-w-sm mx-auto">
            Trouve ton partenaire cinéma idéal parmi les cinéphiles belges
          </p>
        </div>
      </div>

      {/* Right — form */}
      <div className="flex-1 lg:max-w-md flex flex-col items-center justify-center px-8 py-12"
        style={{ background: 'var(--bg-secondary)' }}>
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="lg:hidden text-center mb-8">
            <span className="font-display text-4xl tracking-wider">
              CINE<span style={{ color: 'var(--accent-red)' }}>MATCH</span>
            </span>
          </div>

          <h2 className="text-2xl font-semibold text-white mb-2">Connexion</h2>
          <p className="text-[var(--text-muted)] text-sm mb-8">Heureux de te revoir 👋</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="toi@exemple.com"
                required
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[var(--text-muted)] mb-1.5">Mot de passe</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="input-field pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-white"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="px-4 py-3 rounded-lg text-sm text-[var(--accent-red)]"
                style={{ background: 'rgba(230,57,70,0.1)', border: '1px solid rgba(230,57,70,0.2)' }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center flex items-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed mt-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : 'Se connecter'}
            </button>
          </form>

          <p className="text-center text-sm text-[var(--text-muted)] mt-6">
            Pas encore de compte ?{' '}
            <Link to="/register" className="font-medium hover:underline" style={{ color: 'var(--accent-red)' }}>
              Créer un compte
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
