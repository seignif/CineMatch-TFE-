import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'

export default function VerifyEmail() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) return
    authApi.verifyEmail(token)
      .then(() => {
        setStatus('success')
        setMessage('Email vérifié ! Bienvenue sur CineMatch.')
        setTimeout(() => navigate('/'), 3000)
      })
      .catch((err: { response?: { data?: { error?: string } } }) => {
        setStatus('error')
        setMessage(err.response?.data?.error || 'Lien invalide ou expiré.')
      })
  }, [token, navigate])

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center',
      justifyContent: 'center', background: 'var(--bg-primary)', padding: '16px',
    }}>
      <div style={{
        background: 'var(--bg-card)', padding: '40px', borderRadius: '16px',
        textAlign: 'center', maxWidth: '400px', width: '100%',
        border: '1px solid rgba(255,255,255,0.06)',
      }}>
        <h1 className="font-display text-3xl tracking-wider mb-6" style={{ color: 'var(--accent-red)' }}>
          CINEMATCH
        </h1>

        {status === 'loading' && (
          <>
            <div className="w-10 h-10 border-2 border-white/20 border-t-[var(--accent-red)] rounded-full animate-spin mx-auto mb-4" />
            <p style={{ color: 'var(--text-muted)' }}>Vérification en cours...</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="text-5xl mb-4">✅</div>
            <h2 className="text-xl font-semibold text-white mb-2">Email vérifié !</h2>
            <p style={{ color: 'var(--text-muted)' }}>{message}</p>
            <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
              Redirection dans 3 secondes...
            </p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="text-5xl mb-4">❌</div>
            <h2 className="text-xl font-semibold text-white mb-2">Lien invalide</h2>
            <p style={{ color: 'var(--text-muted)' }} className="mb-6">{message}</p>
            <button onClick={() => navigate('/profile')} className="btn-primary">
              Renvoyer depuis mon profil
            </button>
          </>
        )}
      </div>
    </div>
  )
}
