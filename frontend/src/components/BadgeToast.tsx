import { useState, useEffect } from 'react'
import type { Badge } from '../types'

const BADGE_SVG_MAP: Record<string, string> = {
  badge_clap: '/assets/badges/badge_clap.svg',
  badge_star: '/assets/badges/badge_star.svg',
  badge_masks: '/assets/badges/badge_masks.svg',
  badge_trophy: '/assets/badges/badge_trophy.svg',
  badge_popcorn: '/assets/badges/badge_popcorn.svg',
  badge_reel: '/assets/badges/badge_reel.svg',
  badge_camera: '/assets/badges/badge_camera.svg',
}

interface BadgeToastProps {
  badge: Badge
  onClose: () => void
}

export function BadgeToast({ badge, onClose }: BadgeToastProps) {
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const t = setTimeout(() => {
      setVisible(false)
      setTimeout(onClose, 300)
    }, 5000)
    return () => clearTimeout(t)
  }, [onClose])

  const handleClose = () => {
    setVisible(false)
    setTimeout(onClose, 300)
  }

  return (
    <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-4 px-4 py-3 rounded-xl
      shadow-[0_0_30px_rgba(255,215,0,0.25)] transition-all duration-300
      ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
      style={{ background: 'var(--bg-card)', border: '1px solid rgba(255,215,0,0.4)' }}>
      <img
        src={BADGE_SVG_MAP[badge.svg_id]}
        alt={badge.name}
        className="w-14 h-14 drop-shadow-[0_0_10px_rgba(255,215,0,0.8)]"
      />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold" style={{ color: 'var(--accent-gold)' }}>
          Nouveau badge débloqué !
        </p>
        <p className="text-white font-bold text-sm">{badge.name}</p>
        <p className="text-[var(--text-muted)] text-xs truncate">{badge.description}</p>
      </div>
      <button
        onClick={handleClose}
        className="text-[var(--text-muted)] hover:text-white text-lg leading-none ml-1">
        ✕
      </button>
    </div>
  )
}
