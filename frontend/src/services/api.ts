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
  getAll: (params?: {
    search?: string
    is_future?: boolean
    page?: number
    genre?: string
    min_rating?: number
    show_events?: string
    max_age?: string
  }) => api.get('/films/films/', { params }),
  getById: (id: number) => api.get(`/films/films/${id}/`),
  getSeances: (id: number, params?: { language?: string }) =>
    api.get(`/films/films/${id}/seances/`, { params }),
  tmdbSearch: (q: string, signal?: AbortSignal) => api.get('/films/films/tmdb-search/', { params: { q }, signal }),
  getGenres: () => api.get('/films/films/genres/'),
  getReviews: (filmId: number) => api.get(`/films/films/${filmId}/reviews/`),
}

export const watchedApi = {
  getAll: () => api.get('/films/watched/'),
  getStats: () => api.get('/films/watched/stats/'),
  create: (data: {
    film_id: number
    rating?: number | null
    review?: string
    watched_date?: string | null
    is_public?: boolean
  }) => api.post('/films/watched/', data),
  update: (id: number, data: object) => api.patch(`/films/watched/${id}/`, data),
  delete: (id: number) => api.delete(`/films/watched/${id}/`),
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
  verifyEmail: (token: string) => api.get(`/auth/verify-email/${token}/`),
  resendVerification: () => api.post('/auth/resend-verification/'),
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

export const groupsApi = {
  getAll: () => api.get('/matching/groups/'),
  getInvitations: () => api.get('/matching/groups/invitations/'),
  getById: (id: number) => api.get(`/matching/groups/${id}/`),
  update: (id: number, data: { name: string }) =>
    api.patch(`/matching/groups/${id}/`, data),
  create: (data: { name?: string; member_ids: number[] }) =>
    api.post('/matching/groups/', data),
  respond: (id: number, action: 'accept' | 'decline') =>
    api.post(`/matching/groups/${id}/respond/`, { action }),
  leave: (id: number) => api.post(`/matching/groups/${id}/leave/`),
  getMessages: (id: number) => api.get(`/matching/groups/${id}/messages/`),
  vote: (id: number, film_id: number, vote: 'up' | 'down') =>
    api.post(`/matching/groups/${id}/vote/`, { film_id, vote }),
  chooseFilm: (id: number, film_id: number) =>
    api.post(`/matching/groups/${id}/choose-film/`, { film_id }),
  invite: (id: number, member_ids: number[]) =>
    api.post(`/matching/groups/${id}/invite/`, { member_ids }),
  removeMember: (groupId: number, userId: number) =>
    api.delete(`/matching/groups/${groupId}/members/${userId}/`),
}

export const chatApi = {
  getConversations: () => api.get('/chat/conversations/'),
  createConversation: (match_id: number) =>
    api.post('/chat/conversations/create/', { match_id }),
  getMessages: (conv_id: number) =>
    api.get(`/chat/conversations/${conv_id}/messages/`),
  getUnreadCount: () => api.get('/chat/unread/'),
}

export const socialApi = {
  getPosts: (params?: { film_id?: number; matches_only?: boolean }) =>
    api.get('/social/posts/', { params }),
  getPost: (id: number) => api.get(`/social/posts/${id}/`),
  createPost: (data: { content: string; film_id?: number }) =>
    api.post('/social/posts/', data),
  deletePost: (id: number) => api.delete(`/social/posts/${id}/`),
  toggleLike: (postId: number) => api.post(`/social/posts/${postId}/like/`),
  getComments: (postId: number) => api.get(`/social/posts/${postId}/comments/`),
  addComment: (postId: number, content: string) =>
    api.post(`/social/posts/${postId}/comments/`, { content }),
  deleteComment: (commentId: number) => api.delete(`/social/comments/${commentId}/`),
  getNotifications: () => api.get('/social/notifications/'),
  getUnreadCount: () => api.get('/social/notifications/unread-count/'),
  markAllRead: () => api.post('/social/notifications/read/'),
  markOneRead: (id: number) => api.post(`/social/notifications/${id}/read/`),
}

export default api
