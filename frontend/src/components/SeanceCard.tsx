import { ExternalLink, Sofa } from 'lucide-react'
import type { Seance } from '../types'

interface SeanceCardProps {
  seance: Seance
}

function formatShowtime(isoString: string) {
  const date = new Date(isoString)
  const days = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
  const months = ['jan', 'fév', 'mar', 'avr', 'mai', 'jun', 'jul', 'aoû', 'sep', 'oct', 'nov', 'déc']
  const day = days[date.getDay()]
  const dateNum = date.getDate()
  const month = months[date.getMonth()]
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return { label: `${day} ${dateNum} ${month}`, time: `${hours}h${minutes}` }
}

function parseAttributes(raw: string) {
  if (!raw) return []
  return raw.split(',').map(s => s.trim()).filter(Boolean)
}

export default function SeanceCard({ seance }: SeanceCardProps) {
  const { label, time } = formatShowtime(seance.showtime)
  const attrs = parseAttributes(seance.raw_attributes)

  return (
    <div className="glass rounded-xl p-4 flex items-center gap-4 hover:border-[var(--accent-red)] transition-colors"
      style={{ borderColor: seance.is_sold_out ? 'rgba(255,255,255,0.05)' : undefined }}>

      {/* Heure */}
      <div className="text-center min-w-[60px]">
        <span className="font-display text-3xl leading-none" style={{ color: 'var(--accent-red)' }}>
          {time}
        </span>
        <p className="text-[10px] text-[var(--text-muted)] mt-0.5">{label}</p>
      </div>

      {/* Infos */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{seance.cinema.name}</p>
        <div className="flex items-center gap-2 mt-1 flex-wrap">
          <span className="text-xs px-2 py-0.5 rounded"
            style={{ background: 'rgba(255,255,255,0.08)', color: 'var(--text-muted)' }}>
            {seance.language || 'FR'}
          </span>
          {seance.hall && (
            <span className="text-xs text-[var(--text-muted)]">Salle {seance.hall}</span>
          )}
          {seance.has_cosy_seating && (
            <span className="flex items-center gap-1 text-xs text-[var(--accent-gold)]">
              <Sofa size={11} /> Cosy
            </span>
          )}
          {attrs.map((a, i) => (
            <span key={i} className="text-xs text-[var(--text-muted)] uppercase font-mono">{a}</span>
          ))}
        </div>
      </div>

      {/* Bouton */}
      {seance.is_sold_out ? (
        <span className="badge-red shrink-0">Complet</span>
      ) : (
        <a
          href={seance.booking_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={e => e.stopPropagation()}
          className="shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium text-white transition-all hover:-translate-y-0.5"
          style={{ background: 'var(--accent-red)' }}
        >
          Réserver
          <ExternalLink size={13} />
        </a>
      )}
    </div>
  )
}
