const BACKEND = (import.meta.env.VITE_API_BASE_URL?.replace('/api', '') || 'http://localhost:8000').replace('http://', 'https://')

export function mediaUrl(path: string | null | undefined): string | null {
  if (!path) return null
  if (path.startsWith('http')) return path
  return `${BACKEND}${path}`
}
