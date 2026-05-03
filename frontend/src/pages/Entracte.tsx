import { useEffect, useState, useCallback } from 'react'
import { PenSquare } from 'lucide-react'
import type { Post } from '../types'
import api, { socialApi } from '../services/api'
import { PostCard } from '../components/PostCard'
import { CreatePostModal } from '../components/CreatePostModal'

type FeedTab = 'all' | 'matches'

export default function Entracte() {
  const [posts, setPosts] = useState<Post[]>([])
  const [tab, setTab] = useState<FeedTab>('all')
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [nextUrl, setNextUrl] = useState<string | null>(null)
  const [loadingMore, setLoadingMore] = useState(false)

  const fetchPosts = useCallback(async (selectedTab: FeedTab) => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = {}
      if (selectedTab === 'matches') params.matches_only = true
      const res = await socialApi.getPosts(params)
      const data = res.data
      if (data.results !== undefined) {
        setPosts(data.results)
        setNextUrl(data.next ?? null)
      } else {
        setPosts(data)
        setNextUrl(null)
      }
    } catch {
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchPosts(tab)
  }, [tab, fetchPosts])

  const handleLoadMore = async () => {
    if (!nextUrl || loadingMore) return
    setLoadingMore(true)
    try {
      const res = await api.get(nextUrl)
      setPosts(prev => [...prev, ...(res.data.results ?? res.data)])
      setNextUrl(res.data.next ?? null)
    } catch {
    } finally {
      setLoadingMore(false)
    }
  }

  const handlePostCreated = (post: Post) => {
    setPosts(prev => [post, ...prev])
  }

  const handlePostDeleted = (id: number) => {
    setPosts(prev => prev.filter(p => p.id !== id))
  }

  const tabs: { key: FeedTab; label: string }[] = [
    { key: 'all', label: 'Tous' },
    { key: 'matches', label: 'Mes matchs' },
  ]

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-display font-bold text-white tracking-wider uppercase">
          L'Entracte
        </h1>
        <p className="text-[var(--text-muted)] text-sm mt-1">
          Partagez vos coups de coeur avec la communauté
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-5">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-[var(--accent-red)] text-white'
                : 'bg-white/5 text-[var(--text-muted)] hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Feed */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-[var(--bg-card)] rounded-xl p-4 animate-pulse">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-9 h-9 rounded-full bg-white/10" />
                <div className="flex-1 space-y-1">
                  <div className="h-3 bg-white/10 rounded w-24" />
                  <div className="h-2 bg-white/10 rounded w-16" />
                </div>
              </div>
              <div className="space-y-2">
                <div className="h-3 bg-white/10 rounded" />
                <div className="h-3 bg-white/10 rounded w-3/4" />
              </div>
            </div>
          ))}
        </div>
      ) : posts.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-4xl mb-3">🎭</p>
          <p className="text-white font-semibold mb-1">
            {tab === 'matches' ? 'Aucun post de vos matchs' : 'Soyez le premier à poster !'}
          </p>
          <p className="text-[var(--text-muted)] text-sm">
            Partagez votre avis sur un film avec la communauté
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {posts.map(post => (
            <PostCard
              key={post.id}
              post={post}
              onDelete={handlePostDeleted}
            />
          ))}
          {nextUrl && (
            <button
              onClick={handleLoadMore}
              disabled={loadingMore}
              className="w-full py-3 text-[var(--text-muted)] hover:text-white text-sm transition-colors"
            >
              {loadingMore ? 'Chargement...' : 'Voir plus'}
            </button>
          )}
        </div>
      )}

      {/* Bouton flottant */}
      <button
        onClick={() => setShowModal(true)}
        className="fixed bottom-20 right-5 w-14 h-14 bg-[var(--accent-red)] rounded-full flex items-center justify-center shadow-lg hover:bg-[var(--accent-red)]/80 transition-colors z-40"
      >
        <PenSquare size={22} className="text-white" />
      </button>

      {showModal && (
        <CreatePostModal
          onClose={() => setShowModal(false)}
          onCreated={handlePostCreated}
        />
      )}
    </div>
  )
}
