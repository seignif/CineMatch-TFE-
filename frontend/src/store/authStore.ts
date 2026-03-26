import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, AuthTokens } from '../types'
import { authApi, usersApi } from '../services/api'

interface AuthState {
  user: User | null
  tokens: AuthTokens | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: object) => Promise<void>
  logout: () => Promise<void>
  fetchMe: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const res = await authApi.login({ email, password })
        const { access, refresh } = res.data
        localStorage.setItem('access_token', access)
        localStorage.setItem('refresh_token', refresh)
        set({ tokens: { access, refresh }, isAuthenticated: true })
        await get().fetchMe()
      },

      register: async (data) => {
        const res = await authApi.register(data)
        const { tokens } = res.data
        localStorage.setItem('access_token', tokens.access)
        localStorage.setItem('refresh_token', tokens.refresh)
        set({ tokens, isAuthenticated: true })
        await get().fetchMe()
      },

      logout: async () => {
        const refresh = localStorage.getItem('refresh_token')
        if (refresh) await authApi.logout(refresh).catch(() => {})
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, tokens: null, isAuthenticated: false })
      },

      fetchMe: async () => {
        const res = await usersApi.me()
        set({ user: res.data })
      },
    }),
    { name: 'auth-store', partialize: (state) => ({ tokens: state.tokens, isAuthenticated: state.isAuthenticated }) }
  )
)
