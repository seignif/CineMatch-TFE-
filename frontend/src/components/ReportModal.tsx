import { useState } from 'react'
import { X, AlertTriangle } from 'lucide-react'

const REASONS = [
  { value: 'harassment', label: 'Harcèlement' },
  { value: 'racism', label: 'Contenu raciste ou discriminatoire' },
  { value: 'sexual', label: 'Contenu sexuel non sollicité' },
  { value: 'spam', label: 'Spam' },
  { value: 'misinformation', label: 'Fausses informations' },
  { value: 'other', label: 'Autre' },
]

interface Props {
  type: 'message' | 'post' | 'comment'
  onClose: () => void
  onSubmit: (reason: string, description: string) => Promise<void>
}

export function ReportModal({ type, onClose, onSubmit }: Props) {
  const [reason, setReason] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const typeLabel = type === 'message' ? 'message' : type === 'post' ? 'post' : 'commentaire'

  const handleSubmit = async () => {
    if (!reason || loading) return
    setLoading(true)
    try {
      await onSubmit(reason, description)
      setDone(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.7)' }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-2xl p-6 space-y-4"
        style={{ background: 'var(--bg-card)', border: '1px solid rgba(255,255,255,0.08)' }}
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle size={18} style={{ color: 'var(--accent-red)' }} />
            <h3 className="text-white font-semibold">Signaler ce {typeLabel}</h3>
          </div>
          <button onClick={onClose} className="text-[var(--text-muted)] hover:text-white transition-colors">
            <X size={18} />
          </button>
        </div>

        {done ? (
          <div className="py-6 text-center space-y-2">
            <p className="text-green-400 font-medium">Signalement envoyé</p>
            <p className="text-[var(--text-muted)] text-sm">
              Merci de nous aider à maintenir une communauté respectueuse.
              Notre équipe examinera ce contenu.
            </p>
            <button onClick={onClose} className="btn-secondary text-sm mt-4">Fermer</button>
          </div>
        ) : (
          <>
            <p className="text-[var(--text-muted)] text-sm">
              Aidez-nous à maintenir une communauté bienveillante.
              Votre signalement sera examiné par notre équipe.
            </p>

            <div className="space-y-2">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider">Motif</p>
              {REASONS.map(r => (
                <label key={r.value}
                  className="flex items-center gap-3 p-2.5 rounded-lg cursor-pointer transition-colors"
                  style={{
                    background: reason === r.value ? 'rgba(230,57,70,0.1)' : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${reason === r.value ? 'rgba(230,57,70,0.3)' : 'rgba(255,255,255,0.05)'}`,
                  }}>
                  <input
                    type="radio"
                    name="reason"
                    value={r.value}
                    checked={reason === r.value}
                    onChange={() => setReason(r.value)}
                    className="accent-[var(--accent-red)]"
                  />
                  <span className="text-sm text-white">{r.label}</span>
                </label>
              ))}
            </div>

            <div>
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
                Détails supplémentaires (optionnel)
              </p>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Décrivez le problème..."
                maxLength={500}
                rows={2}
                className="input-field resize-none text-sm"
              />
            </div>

            <div className="flex gap-3 pt-1">
              <button onClick={onClose} className="flex-1 btn-secondary text-sm">
                Annuler
              </button>
              <button
                onClick={handleSubmit}
                disabled={!reason || loading}
                className="flex-1 py-2 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-40"
                style={{ background: 'var(--accent-red)' }}
              >
                {loading ? 'Envoi...' : 'Signaler'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
