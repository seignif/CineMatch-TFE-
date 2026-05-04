import type { CastMember, CrewMember } from '../types'

interface Props {
  cast: CastMember[]
  crew: CrewMember[]
}

const PLACEHOLDER = '/default-avatar.png'

export function FilmCast({ cast, crew }: Props) {
  if (!cast?.length && !crew?.length) return null

  const director = crew?.find(c => c.job === 'Director')
  const writers = crew?.filter(c => ['Screenplay', 'Writer', 'Story'].includes(c.job)) ?? []

  return (
    <div className="mt-10 space-y-8">
      {/* Équipe technique */}
      {(director || writers.length > 0) && (
        <div className="flex flex-wrap gap-8">
          {director && (
            <div>
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-widest mb-2">
                Réalisateur
              </p>
              <div className="flex items-center gap-3">
                <img
                  src={director.profile_url || PLACEHOLDER}
                  alt={director.name}
                  onError={e => { e.currentTarget.src = PLACEHOLDER }}
                  className="w-12 h-12 rounded-full object-cover bg-white/10"
                />
                <span className="text-white text-sm font-medium">{director.name}</span>
              </div>
            </div>
          )}
          {writers.length > 0 && (
            <div>
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-widest mb-2">
                Scénario
              </p>
              <div className="flex flex-col gap-1 justify-center h-12">
                {writers.map((w, i) => (
                  <span key={i} className="text-white text-sm font-medium">{w.name}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Têtes d'affiche */}
      {cast?.length > 0 && (
        <div>
          <h3 className="text-white font-semibold text-lg mb-4">Têtes d'affiche</h3>
          <div className="flex gap-4 overflow-x-auto pb-3 scrollbar-thin scrollbar-thumb-[var(--accent-red)] scrollbar-track-transparent">
            {cast.map((actor, i) => (
              <div key={i} className="flex-shrink-0 w-24 text-center">
                <div className="w-24 h-32 rounded-lg overflow-hidden bg-white/10 mb-2">
                  <img
                    src={actor.profile_url || PLACEHOLDER}
                    alt={actor.name}
                    onError={e => { e.currentTarget.src = PLACEHOLDER }}
                    className="w-full h-full object-cover hover:scale-105 transition-transform duration-200"
                  />
                </div>
                <p className="text-white text-xs font-semibold leading-tight">{actor.name}</p>
                {actor.character && (
                  <p className="text-[var(--text-muted)] text-[11px] italic leading-tight mt-0.5">
                    {actor.character}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
