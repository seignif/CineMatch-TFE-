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

export default api
