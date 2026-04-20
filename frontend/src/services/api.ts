import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'
import type { AuthTokens } from '@/types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Injecter le token JWT dans chaque requête
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Refresh automatique du token expiré
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('refresh_token')

      if (refreshToken) {
        try {
          const { data } = await axios.post<AuthTokens>(`${BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          })
          localStorage.setItem('access_token', data.access)
          if (originalRequest.headers) {
            (originalRequest.headers as Record<string, string>).Authorization = `Bearer ${data.access}`
          }
          return api(originalRequest)
        } catch {
          // Refresh échoué → déconnexion
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }

    return Promise.reject(error)
  }
)

export const filmsApi = {
  getAll: (params?: { search?: string; is_future?: boolean; page?: number }) =>
    api.get('/films/films/', { params }),
  getById: (id: number) => api.get(`/films/films/${id}/`),
  getSeances: (id: number) => api.get(`/films/films/${id}/seances/`),
  tmdbSearch: (q: string) => api.get('/films/films/tmdb-search/', { params: { q } }),
}

export const badgesApi = {
  getMyBadges: () => api.get('/users/badges/'),
  getReputation: (userId: number) => api.get(`/users/reputation/${userId}/`),
}

export const reviewsApi = {
  create: (outingId: number, data: { rating: number; would_go_again: boolean; comment?: string }) =>
    api.post(`/matching/outings/${outingId}/review/`, data),
}

export const recommendationsApi = {
  getRecommendations: () => api.get('/users/recommendations/'),
}

export const cinemasApi = {
  getAll: () => api.get('/films/cinemas/'),
}

export const authApi = {
  register: (data: object) => api.post('/auth/register/', data),
  login: (data: object) => api.post('/auth/login/', data),
  logout: (refresh: string) => api.post('/auth/logout/', { refresh }),
}

export const usersApi = {
  me: () => api.get('/users/me/'),
  updateMe: (data: object) => api.patch('/users/me/', data),
  updateProfile: (data: object) => api.patch('/users/me/profile/', data),
  uploadPicture: (file: File) => {
    const form = new FormData()
    form.append('picture', file)
    return api.post('/users/me/picture/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export const matchingApi = {
  getCandidates: () => api.get('/matching/candidates/'),
  swipe: (to_user_id: number, action: 'like' | 'pass' | 'superlike') =>
    api.post('/matching/swipe/', { to_user_id, action }),
  getMatches: () => api.get('/matching/matches/'),
  getMatch: (id: number) => api.get(`/matching/matches/${id}/`),
}

export const outingsApi = {
  getAll: () => api.get('/matching/outings/'),
  getUpcoming: () => api.get('/matching/outings/upcoming/'),
  getById: (id: number) => api.get(`/matching/outings/${id}/`),
  create: (data: {
    match: number
    seance_id?: number | null
    meeting_place?: string
    meeting_time?: string
    proposal_message?: string
  }) => api.post('/matching/outings/', data),
  confirm: (id: number) => api.put(`/matching/outings/${id}/confirm/`, { action: 'confirm' }),
  refuse: (id: number) => api.put(`/matching/outings/${id}/confirm/`, { action: 'refuse' }),
  cancel: (id: number) => api.put(`/matching/outings/${id}/cancel/`),
  markBooked: (id: number) => api.put(`/matching/outings/${id}/booked/`),
  complete: (id: number) => api.put(`/matching/outings/${id}/complete/`),
}

export const chatApi = {
  getConversations: () => api.get('/chat/conversations/'),
  createConversation: (match_id: number) =>
    api.post('/chat/conversations/create/', { match_id }),
  getMessages: (conv_id: number) =>
    api.get(`/chat/conversations/${conv_id}/messages/`),
  getUnreadCount: () => api.get('/chat/unread/'),
}

export default api
