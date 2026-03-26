import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Layout from './components/Layout'
import Films from './pages/Films'
import FilmDetail from './pages/FilmDetail'
import Login from './pages/Login'
import Register from './pages/Register'
import Profile from './pages/Profile'

const Placeholder = ({ name }: { name: string }) => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="text-center">
      <h1 className="font-display text-5xl tracking-wider mb-2">
        CINE<span style={{ color: 'var(--accent-red)' }}>MATCH</span>
      </h1>
      <p className="text-[var(--text-muted)]">Page : {name}</p>
      <p className="text-sm mt-4" style={{ color: 'var(--text-muted)' }}>Sprint 3 — à venir</p>
    </div>
  </div>
)

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/films" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<Layout />}>
          <Route path="/films" element={<Films />} />
          <Route path="/films/:id" element={<FilmDetail />} />
          <Route path="/profile" element={
            <PrivateRoute><Profile /></PrivateRoute>
          } />
          <Route path="/matching" element={<Placeholder name="Matching" />} />
          <Route path="/matches" element={<Placeholder name="Mes matchs" />} />
          <Route path="/chat" element={<Placeholder name="Chat" />} />
          <Route path="/outings" element={<Placeholder name="Sorties planifiées" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
