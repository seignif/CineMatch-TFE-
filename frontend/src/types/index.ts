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

export interface Match {
  id: number
  user1: User
  user2: User
  score_compatibilite: number
  raisons_compatibilite: string[]
  status: 'active' | 'blocked' | 'expired'
  created_at: string
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
