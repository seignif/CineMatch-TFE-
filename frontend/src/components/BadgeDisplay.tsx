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

const SIZE_MAP = {
  sm: 'w-12 h-12',
  md: 'w-20 h-20',
  lg: 'w-28 h-28',
}

interface BadgeDisplayProps {
  badge: Badge
  size?: 'sm' | 'md' | 'lg'
}

export function BadgeDisplay({ badge, size = 'md' }: BadgeDisplayProps) {
  const svgPath = BADGE_SVG_MAP[badge.svg_id]

  return (
    <div className={`relative group ${SIZE_MAP[size]}`}>
      <img
        src={svgPath}
        alt={badge.name}
        className={`w-full h-full transition-all duration-300 ${
          badge.earned
            ? 'opacity-100 drop-shadow-[0_0_8px_rgba(255,215,0,0.6)]'
            : 'opacity-25 grayscale'
        }`}
      />
      {!badge.earned && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl">🔒</span>
        </div>
      )}
      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-40
        bg-gray-900 text-white text-xs rounded-lg px-3 py-2
        opacity-0 group-hover:opacity-100 transition-opacity duration-200
        pointer-events-none z-20 border border-yellow-500/30 text-center">
        <p className="font-bold mb-0.5">{badge.name}</p>
        <p className="text-gray-300 text-[10px]">{badge.description}</p>
        {!badge.earned && (
          <p className="text-yellow-500 text-[10px] mt-1">Non débloqué</p>
        )}
      </div>
    </div>
  )
}

export function BadgesGrid({ badges }: { badges: Badge[] }) {
  const earned = badges.filter(b => b.earned)
  const locked = badges.filter(b => !b.earned)

  return (
    <div>
      {earned.length > 0 && (
        <div className="mb-6">
          <p className="text-xs font-medium uppercase tracking-wider mb-3"
            style={{ color: 'var(--accent-gold)' }}>
            Badges obtenus ({earned.length})
          </p>
          <div className="flex flex-wrap gap-4">
            {earned.map(badge => (
              <BadgeDisplay key={badge.id} badge={badge} size="lg" />
            ))}
          </div>
        </div>
      )}
      {locked.length > 0 && (
        <div>
          <p className="text-xs font-medium uppercase tracking-wider mb-3 text-[var(--text-muted)]">
            À débloquer ({locked.length})
          </p>
          <div className="flex flex-wrap gap-3">
            {locked.map(badge => (
              <BadgeDisplay key={badge.id} badge={badge} size="md" />
            ))}
          </div>
        </div>
      )}
      {badges.length === 0 && (
        <p className="text-[var(--text-muted)] text-sm">Chargement des badges...</p>
      )}
    </div>
  )
}
