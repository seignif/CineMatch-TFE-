import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Send, Users, Film, MessageCircle, ThumbsUp, ThumbsDown, Search, Check, LogOut, X, Pencil, UserPlus } from 'lucide-react'
import { groupsApi, matchingApi, filmsApi } from '../services/api'
import { useAuthStore } from '../store/authStore'
import { useGroupChat } from '../hooks/useGroupChat'
import type { Group, Film as FilmType, Match } from '../types'

type Tab = 'members' | 'film' | 'chat'

export default function GroupView() {
  const { id } = useParams<{ id: string }>()
  const groupId = Number(id)
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [group, setGroup] = useState<Group | null>(null)
  const [tab, setTab] = useState<Tab>('chat')
  const [input, setInput] = useState('')
  const [filmSearch, setFilmSearch] = useState('')
  const [filmResults, setFilmResults] = useState<FilmType[]>([])
  const [searching, setSearching] = useState(false)
  const [votingFilm, setVotingFilm] = useState<number | null>(null)
  const [leaving, setLeaving] = useState(false)
  const [editingName, setEditingName] = useState(false)
  const [nameInput, setNameInput] = useState('')
  const [savingName, setSavingName] = useState(false)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [matches, setMatches] = useState<Match[]>([])
  const [selectedInviteIds, setSelectedInviteIds] = useState<number[]>([])
  const [inviting, setInviting] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { messages, connected, sendMessage } = useGroupChat(group ? groupId : null)

  const fetchGroup = async () => {
    try {
      const res = await groupsApi.getById(groupId)
      setGroup(res.data)
    } catch { navigate('/groups') }
  }

  useEffect(() => { fetchGroup() }, [groupId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const text = input.trim()
    if (!text) return
    sendMessage(text)
    setInput('')
  }

  const handleFilmSearch = async (q: string) => {
    setFilmSearch(q)
    if (q.length < 2) { setFilmResults([]); return }
    setSearching(true)
    try {
      const res = await filmsApi.getAll({ search: q, is_future: false })
      setFilmResults(res.data.results?.slice(0, 8) ?? [])
    } catch {}
    finally { setSearching(false) }
  }

  const handleVote = async (filmId: number, vote: 'up' | 'down') => {
    setVotingFilm(filmId)
    try {
      const res = await groupsApi.vote(groupId, filmId, vote)
      if (res.data.film_chosen) await fetchGroup()
      else await fetchGroup()
    } catch {}
    finally { setVotingFilm(null) }
  }

  const handleChooseFilm = async (filmId: number) => {
    try {
      await groupsApi.chooseFilm(groupId, filmId)
      await fetchGroup()
    } catch {}
  }

  const handleSaveName = async () => {
    if (!nameInput.trim()) return
    setSavingName(true)
    try {
      await groupsApi.update(groupId, { name: nameInput.trim() })
      await fetchGroup()
      setEditingName(false)
    } catch {}
    finally { setSavingName(false) }
  }

  const handleLeave = async () => {
    if (!confirm('Quitter le groupe ?')) return
    setLeaving(true)
    try {
      await groupsApi.leave(groupId)
      navigate('/groups')
    } catch {}
    finally { setLeaving(false) }
  }

  const handleOpenInvite = async () => {
    try {
      const res = await matchingApi.getMatches()
      setMatches(res.data.results ?? res.data)
    } catch {}
    setSelectedInviteIds([])
    setShowInviteModal(true)
  }

  const toggleInviteId = (id: number) => {
    setSelectedInviteIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  const handleInvite = async () => {
    if (!selectedInviteIds.length) return
    setInviting(true)
    try {
      await groupsApi.invite(groupId, selectedInviteIds)
      setShowInviteModal(false)
      await fetchGroup()
    } catch {}
    finally { setInviting(false) }
  }

  if (!group) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[var(--accent-red)] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const tabs: { id: Tab; label: string; icon: typeof Users }[] = [
    { id: 'members', label: 'Membres', icon: Users },
    { id: 'film', label: 'Film', icon: Film },
    { id: 'chat', label: 'Chat', icon: MessageCircle },
  ]

  const existingMemberIds = new Set(group?.members_info.map(m => m.user_info.id) ?? [])
  const invitableMatches = matches.filter(m => !existingMemberIds.has(m.other_user.id))

  return (
    <div className="min-h-screen flex flex-col max-w-2xl mx-auto">
      {/* Modale invitation */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center px-0 sm:px-4"
          style={{ background: 'rgba(0,0,0,0.85)' }}
          onClick={() => setShowInviteModal(false)}>
          <div className="w-full sm:max-w-sm rounded-t-3xl sm:rounded-2xl overflow-hidden"
            style={{ background: 'var(--bg-card)', border: '1px solid rgba(255,255,255,0.08)', maxHeight: '80vh' }}
            onClick={e => e.stopPropagation()}>
            <div className="px-5 pt-5 pb-3 border-b border-white/5 flex items-center justify-between">
              <h3 className="text-white font-semibold">Inviter des membres</h3>
              <button onClick={() => setShowInviteModal(false)} className="text-[var(--text-muted)] hover:text-white">
                <X size={18} />
              </button>
            </div>
            <div className="overflow-y-auto px-4 py-3 space-y-2" style={{ maxHeight: 'calc(80vh - 130px)' }}>
              {invitableMatches.length === 0 ? (
                <p className="text-sm text-[var(--text-muted)] text-center py-6">
                  Tous vos matchs sont déjà dans le groupe.
                </p>
              ) : (
                invitableMatches.map(m => {
                  const other = m.other_user
                  const selected = selectedInviteIds.includes(other.id)
                  return (
                    <button key={other.id} onClick={() => toggleInviteId(other.id)}
                      className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${selected ? 'ring-1 ring-[var(--accent-red)]' : 'glass hover:bg-white/5'}`}
                      style={selected ? { background: 'rgba(230,57,70,0.1)' } : {}}>
                      <div className="w-9 h-9 rounded-full bg-[var(--accent-red)] flex items-center justify-center text-sm font-bold shrink-0">
                        {other.first_name[0]?.toUpperCase()}
                      </div>
                      <div className="flex-1 text-left">
                        <p className="text-white text-sm font-medium">{other.first_name}</p>
                        {other.city && <p className="text-xs text-[var(--text-muted)]">{other.city}</p>}
                      </div>
                      {selected && <Check size={16} className="text-[var(--accent-red)] shrink-0" />}
                    </button>
                  )
                })
              )}
            </div>
            <div className="px-4 pb-5 pt-3 border-t border-white/5">
              <button onClick={handleInvite} disabled={!selectedInviteIds.length || inviting}
                className="btn-primary w-full py-2.5 text-sm disabled:opacity-50">
                {inviting ? 'Envoi...' : `Inviter ${selectedInviteIds.length > 0 ? `(${selectedInviteIds.length})` : ''}`}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Header */}
      <div className="px-4 pt-6 pb-4">
        <div className="flex items-center gap-3 mb-4">
          <button onClick={() => navigate('/groups')} className="text-[var(--text-muted)] hover:text-white">
            <ArrowLeft size={20} />
          </button>
          <div className="flex-1 min-w-0">
            {editingName ? (
              <div className="flex items-center gap-2">
                <input
                  autoFocus
                  value={nameInput}
                  onChange={e => setNameInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handleSaveName(); if (e.key === 'Escape') setEditingName(false) }}
                  className="input-field flex-1 py-1 text-sm font-display tracking-wider"
                />
                <button onClick={handleSaveName} disabled={savingName}
                  className="text-green-400 hover:text-green-300 transition-colors">
                  <Check size={16} />
                </button>
                <button onClick={() => setEditingName(false)}
                  className="text-[var(--text-muted)] hover:text-white transition-colors">
                  <X size={16} />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <h1 className="text-white font-display text-xl tracking-wider truncate">{group.name}</h1>
                {group.is_creator && (
                  <button onClick={() => { setNameInput(group.name); setEditingName(true) }}
                    className="text-[var(--text-muted)] hover:text-white transition-colors shrink-0">
                    <Pencil size={13} />
                  </button>
                )}
              </div>
            )}
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs text-[var(--text-muted)]">{group.active_member_count} membres</span>
              <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
              <span className="text-xs text-[var(--text-muted)]">{connected ? 'Connecté' : 'Déconnecté'}</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 glass rounded-lg p-1">
          {tabs.map(({ id: tid, label, icon: Icon }) => (
            <button
              key={tid}
              onClick={() => setTab(tid)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-md text-sm font-medium transition-colors ${
                tab === tid ? 'bg-[var(--accent-red)] text-white' : 'text-[var(--text-muted)] hover:text-white'
              }`}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab: Membres */}
      {tab === 'members' && (
        <div className="flex-1 px-4 space-y-3 overflow-y-auto pb-6">
          {group.is_creator && (
            <button onClick={handleOpenInvite}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm glass hover:bg-white/5 transition-colors"
              style={{ color: 'var(--accent-red)', border: '1px dashed rgba(230,57,70,0.4)' }}>
              <UserPlus size={15} />
              Inviter des membres
            </button>
          )}
          {group.members_info.map(member => (
            <div key={member.id} className="glass rounded-xl p-3 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[var(--accent-red)] flex items-center justify-center text-sm font-bold shrink-0">
                {member.user_info.first_name[0]?.toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-medium">{member.user_info.first_name}</p>
                {member.user_info.city && <p className="text-xs text-[var(--text-muted)]">{member.user_info.city}</p>}
              </div>
              <div className="flex items-center gap-2">
                {member.role === 'admin' && (
                  <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: 'rgba(255,215,0,0.15)', color: 'var(--accent-gold)' }}>Admin</span>
                )}
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  member.status === 'accepted' ? 'text-green-400 bg-green-400/10'
                  : member.status === 'pending' ? 'text-yellow-400 bg-yellow-400/10'
                  : 'text-red-400 bg-red-400/10'
                }`}>
                  {member.status === 'accepted' ? 'Accepté' : member.status === 'pending' ? 'En attente' : 'Refusé'}
                </span>
              </div>
            </div>
          ))}

          {group.creator !== user?.id && (
            <button
              onClick={handleLeave}
              disabled={leaving}
              className="w-full mt-4 flex items-center justify-center gap-2 py-3 rounded-xl text-sm text-[var(--text-muted)] hover:text-red-400 glass transition-colors"
            >
              <LogOut size={15} />
              Quitter le groupe
            </button>
          )}
        </div>
      )}

      {/* Tab: Film */}
      {tab === 'film' && (
        <div className="flex-1 px-4 overflow-y-auto pb-6">
          {group.chosen_film_info ? (
            <div className="mb-6">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-3">Film choisi</p>
              <div
                className="glass rounded-xl p-4 flex items-center gap-4 cursor-pointer hover:bg-white/5"
                onClick={() => navigate(`/films/${group.chosen_film_info!.id}`)}
                style={{ border: '1px solid rgba(255,215,0,0.3)' }}
              >
                {group.chosen_film_info.poster_url && (
                  <img src={group.chosen_film_info.poster_url} alt={group.chosen_film_info.title}
                    className="w-14 h-20 object-cover rounded-lg" />
                )}
                <div>
                  <p className="text-white font-medium">{group.chosen_film_info.title}</p>
                  <p className="text-xs mt-1 flex items-center gap-1" style={{ color: 'var(--accent-gold)' }}>
                    <Check size={11} /> Film sélectionné — Voir les séances
                  </p>
                </div>
              </div>
            </div>
          ) : null}

          {/* Votes existants */}
          {group.votes_summary.length > 0 && (
            <div className="mb-6">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-3">Films proposés</p>
              <div className="space-y-3">
                {group.votes_summary.map(({ film, up, down }) => film && (
                  <div key={film.id} className="glass rounded-xl p-3 flex items-center gap-3">
                    {film.poster_url && (
                      <img src={film.poster_url} alt={film.title} className="w-10 h-14 object-cover rounded-lg shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-sm font-medium truncate">{film.title}</p>
                      <div className="flex items-center gap-3 mt-1.5">
                        <button
                          onClick={() => handleVote(film.id, 'up')}
                          disabled={votingFilm === film.id}
                          className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-colors ${
                            group.my_votes?.[String(film.id)] === 'up'
                              ? 'bg-green-400/25 ring-1 ring-green-400/50'
                              : 'glass hover:bg-green-400/10'
                          }`}
                        >
                          <ThumbsUp size={12} className="text-green-400" /> {up}
                        </button>
                        <button
                          onClick={() => handleVote(film.id, 'down')}
                          disabled={votingFilm === film.id}
                          className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-colors ${
                            group.my_votes?.[String(film.id)] === 'down'
                              ? 'bg-red-400/25 ring-1 ring-red-400/50'
                              : 'glass hover:bg-red-400/10'
                          }`}
                        >
                          <ThumbsDown size={12} className="text-red-400" /> {down}
                        </button>
                        <span className="text-xs text-[var(--text-muted)]">/ {group.active_member_count}</span>
                      </div>
                    </div>
                    {group.my_votes?.[String(film.id)] && !group.chosen_film_info && (
                      <button
                        onClick={() => handleVote(film.id, group.my_votes[String(film.id)])}
                        disabled={votingFilm === film.id}
                        title="Retirer ma proposition"
                        className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-red-400 hover:bg-red-400/10 transition-colors"
                      >
                        <X size={14} />
                      </button>
                    )}
                    {group.is_creator && !group.chosen_film_info && (
                      <button
                        onClick={() => handleChooseFilm(film.id)}
                        className="btn-primary px-3 py-1.5 text-xs shrink-0"
                      >
                        Choisir
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recherche film */}
          <div>
            <p className="text-xs text-[var(--text-muted)] uppercase tracking-wider mb-3">Proposer un film</p>
            <div className="relative mb-3">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
              <input
                type="text"
                value={filmSearch}
                onChange={e => handleFilmSearch(e.target.value)}
                placeholder="Rechercher un film..."
                className="input-field pl-9 w-full"
              />
            </div>
            {searching && <p className="text-xs text-[var(--text-muted)]">Recherche...</p>}
            <div className="space-y-2">
              {filmResults.map(film => (
                <div key={film.id} className="glass rounded-xl p-3 flex items-center gap-3">
                  {film.poster_url && (
                    <img src={film.poster_url} alt={film.title} className="w-10 h-14 object-cover rounded-lg shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">{film.title}</p>
                    {film.tmdb_rating && (
                      <p className="text-xs text-[var(--text-muted)]">★ {film.tmdb_rating}</p>
                    )}
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button
                      onClick={() => handleVote(film.id, 'up')}
                      disabled={votingFilm === film.id}
                      className={`flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs transition-colors ${
                        group.my_votes?.[String(film.id)] === 'up'
                          ? 'bg-green-400/25 ring-1 ring-green-400/50'
                          : 'glass hover:bg-green-400/10'
                      }`}
                    >
                      <ThumbsUp size={13} className="text-green-400" />
                    </button>
                    <button
                      onClick={() => handleVote(film.id, 'down')}
                      disabled={votingFilm === film.id}
                      className={`flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs transition-colors ${
                        group.my_votes?.[String(film.id)] === 'down'
                          ? 'bg-red-400/25 ring-1 ring-red-400/50'
                          : 'glass hover:bg-red-400/10'
                      }`}
                    >
                      <ThumbsDown size={13} className="text-red-400" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Chat */}
      {tab === 'chat' && (
        <>
          <div className="flex-1 overflow-y-auto px-4 space-y-2 pb-2">
            {messages.length === 0 && (
              <p className="text-center text-[var(--text-muted)] text-sm py-8">Aucun message pour l'instant.</p>
            )}
            {messages.map(msg => {
              if (msg.is_system) {
                return (
                  <div key={msg.id} className="text-center my-2">
                    <span className="text-xs italic text-[var(--text-muted)]">{msg.content}</span>
                  </div>
                )
              }
              const isMe = msg.sender_id === user?.id
              return (
                <div key={msg.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs rounded-2xl px-4 py-2 ${
                    isMe ? 'rounded-tr-sm text-white' : 'rounded-tl-sm'
                  }`} style={{
                    background: isMe ? 'var(--accent-red)' : 'var(--bg-card)',
                  }}>
                    {!isMe && <p className="text-xs font-medium mb-0.5 text-[var(--text-muted)]">{msg.sender_name}</p>}
                    <p className={`text-sm ${isMe ? 'text-white' : 'text-white'}`}>{msg.content}</p>
                  </div>
                </div>
              )
            })}
            <div ref={messagesEndRef} />
          </div>

          <div className="px-4 pb-6 pt-2">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSend()}
                placeholder="Écrire un message..."
                className="input-field flex-1"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || !connected}
                className="btn-primary px-4 py-2 flex items-center gap-1.5 disabled:opacity-50"
              >
                <Send size={15} />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
