// ---- Auth ----
export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  first_name: string
  last_name: string
  password: string
  password2: string
  date_of_birth?: string
  city?: string
  rgpd_consent: boolean
}

export interface AuthTokens {
  access: string
  refresh: string
}

// ---- User ----
export interface User {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  city: string
  date_of_birth?: string
  profile: UserProfile
}

export interface UserProfile {
  id: number
  bio: string
  profile_picture?: string
  mood: string
  genre_preferences: Record<string, number>
  films_signature: Film[]
  badges: string[]
  stats: Record<string, number>
}

// ---- Films ----
export interface Genre {
  id: number
  tmdb_id: number
  nom: string
}

export interface Film {
  id: number
  tmdb_id: number
  titre: string
  titre_original: string
  synopsis: string
  poster: string
  backdrop: string
  trailer_youtube_key: string
  duree?: number
  date_sortie?: string
  note?: number
  genres: Genre[]
  is_now_playing: boolean
}

export interface Cinema {
  id: number
  allocine_id: string
  name: string
  address: string
  city: string
  postal_code: string
  latitude?: number
  longitude?: number
  website: string
  is_active: boolean
}

export interface Seance {
  id: number
  film: Film
  cinema: Cinema
  date_heure: string
  version: 'VF' | 'VO' | 'VOST'
  format: '2D' | '3D' | 'IMAX' | '4DX'
  places_restantes?: number
  booking_url: string
}

// ---- Matching ----
export type SwipeAction = 'like' | 'pass' | 'superlike'

export interface Match {
  id: number
  user1: User
  user2: User
  score_compatibilite: number
  raisons_compatibilite: string[]
  status: 'active' | 'blocked' | 'expired'
  created_at: string
  conversation?: Conversation
}

export interface PlannedOuting {
  id: number
  match: Match
  seance: Seance
  proposer: User
  status: 'proposed' | 'confirmed' | 'completed' | 'cancelled'
  meeting_place: string
  meeting_time?: string
  proposer_booked: boolean
  partner_booked: boolean
  created_at: string
}

// ---- Chat ----
export interface Conversation {
  id: number
  match: Match
  created_at: string
  messages?: Message[]
}

export interface Message {
  id: number
  conversation: number
  sender: User
  contenu: string
  lu: boolean
  created_at: string
}

// ---- API ----
export interface PaginatedResponse<T> {
  count: number
  next?: string
  previous?: string
  results: T[]
}

export interface ApiError {
  detail?: string
  [key: string]: string | string[] | undefined
}
