import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Heart, MessageCircle, Trash2, AlertTriangle } from 'lucide-react'
import type { Post, PostComment } from '../types'
import { socialApi } from '../services/api'
import { useAuthStore } from '../store/authStore'
import { formatDistanceToNow } from '../utils/dateUtils'
import { mediaUrl } from '../utils/media'
import { ReportModal } from './ReportModal'

interface Props {
  post: Post
  onDelete?: (id: number) => void
}

export const PostCard: React.FC<Props> = ({ post, onDelete }) => {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [showComments, setShowComments] = useState(false)
  const [comments, setComments] = useState<PostComment[]>(post.preview_comments)
  const [needsMoreLoad, setNeedsMoreLoad] = useState(post.preview_comments.length < post.comment_count)
  const [commentInput, setCommentInput] = useState('')
  const [liked, setLiked] = useState(post.is_liked)
  const [likeCount, setLikeCount] = useState(post.like_count)
  const [commentCount, setCommentCount] = useState(post.comment_count)
  const [loadingLike, setLoadingLike] = useState(false)
  const [showReport, setShowReport] = useState(false)

  const handleLike = async () => {
    if (loadingLike) return
    setLoadingLike(true)
    const newLiked = !liked
    setLiked(newLiked)
    setLikeCount(prev => newLiked ? prev + 1 : prev - 1)
    try {
      const res = await socialApi.toggleLike(post.id)
      setLikeCount(res.data.like_count)
    } catch {
      setLiked(!newLiked)
      setLikeCount(prev => newLiked ? prev - 1 : prev + 1)
    } finally {
      setLoadingLike(false)
    }
  }

  const handleToggleComments = async () => {
    if (!showComments && needsMoreLoad && commentCount > 3) {
      try {
        const res = await socialApi.getComments(post.id)
        setComments(res.data.results ?? res.data)
        setNeedsMoreLoad(false)
      } catch {}
    }
    setShowComments(prev => !prev)
  }

  const handleComment = async () => {
    if (!commentInput.trim()) return
    try {
      const res = await socialApi.addComment(post.id, commentInput.trim())
      setComments(prev => [...prev, res.data])
      setCommentCount(prev => prev + 1)
      setCommentInput('')
    } catch {}
  }

  const handleDelete = async () => {
    if (!window.confirm('Supprimer ce post ?')) return
    try {
      await socialApi.deletePost(post.id)
      onDelete?.(post.id)
    } catch {}
  }

  const avatar = (url: string | null | undefined): string =>
    mediaUrl(url) ?? '/default-avatar.svg'

  return (
    <div className="bg-[var(--bg-card)] rounded-xl p-4 border border-white/5">
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <img
          src={avatar(post.author_picture)}
          alt={post.author_name}
          onError={e => { e.currentTarget.src = '/default-avatar.svg' }}
          className="w-9 h-9 rounded-full object-cover bg-white/10"
        />
        <div className="flex-1 min-w-0">
          <p className="text-white font-medium text-sm">{post.author_name}</p>
          <p className="text-[var(--text-muted)] text-xs">{formatDistanceToNow(post.created_at)}</p>
        </div>
        {post.is_author ? (
          <button
            onClick={handleDelete}
            className="text-[var(--text-muted)] hover:text-red-400 transition-colors p-1"
          >
            <Trash2 size={15} />
          </button>
        ) : (
          <button
            onClick={() => setShowReport(true)}
            className="text-[var(--text-muted)] hover:text-orange-400 transition-colors p-1"
            title="Signaler ce post"
          >
            <AlertTriangle size={15} />
          </button>
        )}
      </div>

      {/* Contenu */}
      <p className="text-white/90 text-sm leading-relaxed mb-3 whitespace-pre-wrap">{post.content}</p>

      {/* Film lié */}
      {post.film_info && (
        <div
          className="flex items-center gap-3 bg-black/30 rounded-lg p-2 mb-3 cursor-pointer hover:bg-black/50 transition-colors"
          onClick={() => navigate(`/films/${post.film_info!.id}`)}
        >
          {post.film_info.poster_url && (
            <img
              src={post.film_info.poster_url}
              alt={post.film_info.title}
              className="w-10 h-14 object-cover rounded"
            />
          )}
          <span className="text-[var(--accent-red)] text-sm font-medium">
            {post.film_info.title}
          </span>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-4 pt-2 border-t border-white/5">
        <button
          onClick={handleLike}
          disabled={loadingLike}
          className={`flex items-center gap-1.5 text-sm transition-colors ${
            liked ? 'text-red-400' : 'text-[var(--text-muted)] hover:text-red-400'
          }`}
        >
          <Heart size={16} fill={liked ? 'currentColor' : 'none'} />
          <span>{likeCount}</span>
        </button>

        <button
          onClick={handleToggleComments}
          className="flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-white transition-colors"
        >
          <MessageCircle size={16} />
          <span>{commentCount}</span>
        </button>
      </div>

      {showReport && (
        <ReportModal
          type="post"
          onClose={() => setShowReport(false)}
          onSubmit={async (reason, description) => {
            await socialApi.createReport({
              type: 'post',
              reason,
              description,
              post: post.id,
              reported_user: post.author_id,
            })
          }}
        />
      )}

      {/* Commentaires */}
      {showComments && (
        <div className="mt-3 space-y-2">
          {comments.map(comment => (
            <div key={comment.id} className="flex items-start gap-2">
              <img
                src={avatar(comment.author_picture)}
                alt={comment.author_name}
                onError={e => { e.currentTarget.src = '/default-avatar.svg' }}
                className="w-7 h-7 rounded-full object-cover bg-white/10 flex-shrink-0 mt-0.5"
              />
              <div className="bg-black/30 rounded-lg px-3 py-2 flex-1 min-w-0">
                <span className="text-white text-xs font-medium">{comment.author_name} </span>
                <span className="text-white/80 text-xs">{comment.content}</span>
              </div>
            </div>
          ))}

          {/* Input */}
          <div className="flex items-center gap-2 mt-2">
            <img
              src={avatar(user?.profile?.profile_picture ?? null)}
              alt="Moi"
              onError={e => { e.currentTarget.src = '/default-avatar.svg' }}
              className="w-7 h-7 rounded-full object-cover bg-white/10 flex-shrink-0"
            />
            <input
              type="text"
              value={commentInput}
              onChange={e => setCommentInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleComment()}
              placeholder="Écrire un commentaire..."
              maxLength={280}
              className="flex-1 bg-black/30 border border-white/10 rounded-full px-3 py-1.5 text-white text-xs placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-red)]"
            />
            <button
              onClick={handleComment}
              disabled={!commentInput.trim()}
              className="text-[var(--accent-red)] disabled:opacity-30 transition-opacity text-sm font-medium"
            >
              Envoyer
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
