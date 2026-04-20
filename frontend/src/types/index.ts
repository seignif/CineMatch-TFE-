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
  bio: string
  profile_picture?: string | null
  mood: string
  genre_preferences: Record<string, number>
  films_signature: Film[]
  badges: string[]
  stats: Record<string, number>
}

// ---- Films ----
export interface Genre {
  id: number
  name: string
  tmdb_id?: number | null
}

export interface Film {
  id: number
  kinepolis_id: string
  title: string
  synopsis: string
  short_synopsis: string
  duration: number | null
  release_date: string | null
  language: string
  is_future: boolean
  poster_url: string
  backdrop_url: string
  trailer_youtube_key: string
  tmdb_rating: number | null
  imdb_code: string
  genres: Genre[]
  seances?: Seance[]
}

export interface Cinema {
  id: number
  kinepolis_id: string
  name: string
  country: string
  language: string
  latitude: number | null
  longitude: number | null
  is_active: boolean
}

export interface Seance {
  id: number
  kinepolis_session_id: string
  cinema: Cinema
  showtime: string
  language: string
  hall: number | null
  is_sold_out: boolean
  has_cosy_seating: boolean
  booking_url: string
  raw_attributes: string
}

// ---- Matching ----
export type SwipeAction = 'like' | 'pass' | 'superlike'

export interface CandidateProfile {
  bio: string
  profile_picture: string | null
  mood: string
  genre_preferences: Record<string, number>
}

export interface Candidate {
  id: number
  first_name: string
  city: string
  date_of_birth?: string | null
  profile: CandidateProfile
  score: number
  reasons: string[]
}

export interface Match {
  id: number
  other_user: {
    id: number
    first_name: string
    city: string
    profile: CandidateProfile
  }
  score_compatibilite: number
  raisons_compatibilite: string[]
  ai_generated_reasons: string[]
  ai_match_message: string
  status: 'active' | 'blocked' | 'expired'
  created_at: string
}

// ---- Outings ----
export interface OutingSeance {
  id: number
  film_title: string
  film_poster: string
  cinema_name: string
  cinema_kinepolis_id: string
  showtime: string
  language: string
  hall: number | null
  booking_url: string
  is_sold_out: boolean
  raw_attributes: string
}

export interface OutingUserInfo {
  id: number
  first_name: string
  profile_picture: string | null
}

export interface PlannedOuting {
  id: number
  match: number
  status: 'proposed' | 'confirmed' | 'completed' | 'cancelled'
  seance: OutingSeance | null
  seance_id?: number | null
  proposer_info: OutingUserInfo
  partner_info: OutingUserInfo
  meeting_place: string
  meeting_time: string | null
  proposer_booked: boolean
  partner_booked: boolean
  proposal_message: string
  is_upcoming: boolean
  user_is_proposer: boolean
  created_at: string
  updated_at: string
}

// ---- Badges & Réputation (US-039/040) ----
export interface Badge {
  id: string
  name: string
  description: string
  svg_id: string
  color_primary: string
  color_secondary: string
  tier: 'bronze' | 'silver' | 'gold'
  earned: boolean
}

export interface ReputationScore {
  score: number | null
  count: number
  label: string
  would_go_again_pct: number | null
}

// ---- Recommandations (US-035) ----
export interface FilmRecommendation {
  film: import('./index').Film
  score: number
  reasons: string[]
}

// ---- Chat ----
export interface ChatMessage {
  id: number
  sender_id: number
  sender_name: string
  content: string
  is_read: boolean
  created_at: string
}

export interface Conversation {
  id: number
  other_user: {
    id: number
    first_name: string
    city: string
    profile_picture: string | null
  }
  last_message: {
    content: string
    sender_name: string
    created_at: string
  } | null
  unread_count: number
  match_score: number
  updated_at: string
}

// ---- API ----
export interface PaginatedResponse<T> {
  count: number
  next?: string | null
  previous?: string | null
  results: T[]
}

export interface ApiError {
  detail?: string
  [key: string]: string | string[] | undefined
}
