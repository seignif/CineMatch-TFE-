import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Users, Clock, Check, X, Film } from 'lucide-react'
import { groupsApi, matchingApi } from '../services/api'
import type { Group, Match } from '../types'
import CreateGroupModal from '../components/CreateGroupModal'

function formatRelative(iso: string) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60) return "à l'instant"
  if (diff < 3600) return `il y a ${Math.floor(diff / 60)}min`
  if (diff < 86400) return `il y a ${Math.floor(diff / 3600)}h`
  return `il y a ${Math.floor(diff / 86400)}j`
}

export default function Groups() {
  const navigate = useNavigate()
  const [groups, setGroups] = useState<Group[]>([])
  const [invitations, setInvitations] = useState<Group[]>([])
  const [matches, setMatches] = useState<Match[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [responding, setResponding] = useState<number | null>(null)

  const fetchAll = async () => {
    setLoading(true)
    try {
      const [g, inv, m] = await Promise.all([
        groupsApi.getAll(),
        groupsApi.getInvitations(),
        matchingApi.getMatches(),
      ])
      setGroups(g.data.results ?? g.data)
      setInvitations(inv.data.results ?? inv.data)
      setMatches(m.data.results ?? m.data)
    } catch {}
    finally { setLoading(false) }
  }

  useEffect(() => { fetchAll() }, [])

  const handleRespond = async (groupId: number, action: 'accept' | 'decline') => {
    setResponding(groupId)
    try {
      await groupsApi.respond(groupId, action)
      await fetchAll()
      if (action === 'accept') navigate(`/groups/${groupId}`)
    } catch {}
    finally { setResponding(null) }
  }

  return (
    <div className="min-h-screen px-4 py-8 max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="font-display text-5xl tracking-wider text-white">GROUPES</h1>
        <p className="text-[var(--text-muted)] mt-1">Organise des sorties ciné à plusieurs</p>
      </div>

      {/* Invitations en attente */}
      {invitations.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <Clock size={15} style={{ color: 'var(--accent-gold)' }} />
            <h2 className="text-sm font-medium uppercase tracking-wider" style={{ color: 'var(--accent-gold)' }}>
              Invitations en attente ({invitations.length})
            </h2>
          </div>
          <div className="space-y-3">
            {invitations.map(group => {
              const creator = group.members_info.find(m => m.role === 'admin')
              return (
                <div key={group.id} className="glass rounded-xl p-4" style={{ borderColor: 'rgba(255,215,0,0.2)', border: '1px solid' }}>
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-white font-medium">{group.name}</p>
                      <p className="text-xs text-[var(--text-muted)] mt-0.5">
                        Invité par {creator?.user_info.first_name ?? '—'} · {group.active_member_count} membre{group.active_member_count > 1 ? 's' : ''}
                      </p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <button
                        onClick={() => handleRespond(group.id, 'decline')}
                        disabled={responding === group.id}
                        className="p-2 rounded-lg glass hover:bg-white/5 text-[var(--text-muted)] hover:text-white transition-colors"
                      >
                        <X size={16} />
                      </button>
                      <button
                        onClick={() => handleRespond(group.id, 'accept')}
                        disabled={responding === group.id}
                        className="btn-primary px-4 py-2 text-sm flex items-center gap-1"
                      >
                        <Check size={14} /> Accepter
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Mes groupes */}
      <div className="mb-24">
        <h2 className="text-sm font-medium uppercase tracking-wider text-[var(--text-muted)] mb-3">
          Mes groupes ({groups.length})
        </h2>
        {loading ? (
          <div className="space-y-3">
            {[1,2].map(i => <div key={i} className="h-20 rounded-xl animate-pulse" style={{ background: 'var(--bg-card)' }} />)}
          </div>
        ) : groups.length === 0 ? (
          <div className="text-center py-16">
            <Users size={48} className="mx-auto mb-4 text-[var(--text-muted)]" />
            <p className="text-white font-medium">Aucun groupe pour l'instant</p>
            <p className="text-[var(--text-muted)] text-sm mt-1">Crée un groupe pour organiser une sortie à plusieurs</p>
          </div>
        ) : (
          <div className="space-y-3">
            {groups.map(group => (
              <button
                key={group.id}
                onClick={() => navigate(`/groups/${group.id}`)}
                className="w-full glass rounded-xl p-4 text-left hover:bg-white/5 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
                    style={{ background: 'var(--accent-red)' }}>
                    <Users size={18} className="text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-white font-medium truncate">{group.name}</p>
                      {group.last_message && (
                        <span className="text-xs text-[var(--text-muted)] shrink-0">
                          {formatRelative(group.last_message.created_at)}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-[var(--text-muted)] mt-0.5">
                      {group.active_member_count} membre{group.active_member_count > 1 ? 's' : ''}
                    </p>
                    {group.chosen_film_info && (
                      <div className="flex items-center gap-1 mt-1">
                        <Film size={11} style={{ color: 'var(--accent-gold)' }} />
                        <span className="text-xs truncate" style={{ color: 'var(--accent-gold)' }}>
                          {group.chosen_film_info.title}
                        </span>
                      </div>
                    )}
                    {group.last_message && (
                      <p className="text-xs text-[var(--text-muted)] mt-1 truncate">
                        {group.last_message.is_system
                          ? <em>{group.last_message.content}</em>
                          : <>{group.last_message.sender_name} : {group.last_message.content}</>
                        }
                      </p>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Bouton flottant */}
      <button
        onClick={() => setShowModal(true)}
        className="fixed bottom-6 right-6 btn-primary px-5 py-3 flex items-center gap-2 rounded-full shadow-lg"
      >
        <Plus size={18} />
        Créer un groupe
      </button>

      {showModal && (
        <CreateGroupModal
          matches={matches}
          onClose={() => setShowModal(false)}
          onCreated={(id) => { setShowModal(false); navigate(`/groups/${id}`) }}
        />
      )}
    </div>
  )
}
