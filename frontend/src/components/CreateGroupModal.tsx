import { useState } from 'react'
import { X, Users, Check } from 'lucide-react'
import { groupsApi } from '../services/api'
import type { Match } from '../types'

interface Props {
  matches: Match[]
  onClose: () => void
  onCreated: (groupId: number) => void
}

export default function CreateGroupModal({ matches, onClose, onCreated }: Props) {
  const [name, setName] = useState('')
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const toggle = (userId: number) => {
    setSelectedIds(prev =>
      prev.includes(userId) ? prev.filter(id => id !== userId) : [...prev, userId]
    )
  }

  const handleCreate = async () => {
    if (selectedIds.length === 0) { setError('Sélectionne au moins un match.'); return }
    setLoading(true)
    setError('')
    try {
      const res = await groupsApi.create({ name: name || undefined, member_ids: selectedIds })
      onCreated(res.data.id)
    } catch (e: any) {
      setError(e.response?.data?.error || 'Erreur lors de la création.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.7)' }}>
      <div className="glass rounded-2xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-white font-display text-xl tracking-wider">CRÉER UN GROUPE</h2>
          <button onClick={onClose} className="text-[var(--text-muted)] hover:text-white">
            <X size={20} />
          </button>
        </div>

        <div className="mb-4">
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Nom du groupe (optionnel)"
            className="input-field w-full"
          />
        </div>

        <div className="mb-2 flex items-center justify-between">
          <span className="text-sm text-[var(--text-muted)]">Inviter des matchs</span>
          <span className="text-xs" style={{ color: selectedIds.length >= 7 ? 'var(--accent-red)' : 'var(--text-muted)' }}>
            {selectedIds.length}/7
          </span>
        </div>

        <div className="space-y-2 max-h-64 overflow-y-auto mb-6">
          {matches.map(match => {
            const u = match.other_user
            const selected = selectedIds.includes(u.id)
            const disabled = !selected && selectedIds.length >= 7
            return (
              <button
                key={match.id}
                onClick={() => !disabled && toggle(u.id)}
                disabled={disabled}
                className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors text-left ${
                  selected ? 'bg-[var(--accent-red)]/20 border border-[var(--accent-red)]/40'
                  : disabled ? 'opacity-40 cursor-not-allowed glass'
                  : 'glass hover:bg-white/5'
                }`}
              >
                <div className="w-9 h-9 rounded-full bg-[var(--accent-red)] flex items-center justify-center text-sm font-bold shrink-0">
                  {u.first_name[0]?.toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium">{u.first_name}</p>
                  {u.city && <p className="text-xs text-[var(--text-muted)]">{u.city}</p>}
                </div>
                {selected && <Check size={16} style={{ color: 'var(--accent-red)' }} />}
              </button>
            )
          })}
          {matches.length === 0 && (
            <p className="text-center text-[var(--text-muted)] text-sm py-4">Aucun match disponible.</p>
          )}
        </div>

        {error && <p className="text-sm mb-4" style={{ color: 'var(--accent-red)' }}>{error}</p>}

        <div className="flex gap-3">
          <button onClick={onClose} className="btn-secondary flex-1">Annuler</button>
          <button
            onClick={handleCreate}
            disabled={loading || selectedIds.length === 0}
            className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <Users size={15} />
            {loading ? 'Création...' : 'Créer et inviter'}
          </button>
        </div>
      </div>
    </div>
  )
}
