import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Film, Users, Heart, MessageCircle, Calendar, Menu, X, LogOut, User } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { chatApi, outingsApi } from '../services/api'

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [unread, setUnread] = useState(0)
  const [upcomingOutings, setUpcomingOutings] = useState(0)

  useEffect(() => {
    if (!isAuthenticated) return
    const pollChat = () => chatApi.getUnreadCount().then(r => setUnread(r.data.unread_count)).catch(() => {})
    const pollOutings = () => outingsApi.getUpcoming().then(r => setUpcomingOutings((r.data.results ?? r.data).length)).catch(() => {})
    pollChat()
    pollOutings()
    const t1 = setInterval(pollChat, 30000)
    const t2 = setInterval(pollOutings, 60000)
    return () => { clearInterval(t1); clearInterval(t2) }
  }, [isAuthenticated])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const navLinks = [
    { to: '/films', label: 'Films', icon: Film, badge: 0 },
    { to: '/matching', label: 'Matching', icon: Users, badge: 0 },
    { to: '/matches', label: 'Matchs', icon: Heart, badge: 0 },
    { to: '/outings', label: 'Sorties', icon: Calendar, badge: upcomingOutings },
    { to: '/chat', label: 'Messages', icon: MessageCircle, badge: unread },
  ]

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/films" className="flex items-center gap-2">
          <span className="font-display text-2xl tracking-wider" style={{ color: 'var(--accent-red)' }}>
            CINE<span className="text-white">MATCH</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          {navLinks.map(({ to, label, badge }) => (
            <Link
              key={to}
              to={to}
              className={`relative px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                location.pathname.startsWith(to)
                  ? 'text-white bg-white/10'
                  : 'text-[var(--text-muted)] hover:text-white hover:bg-white/5'
              }`}
            >
              {label}
              {badge > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full text-xs flex items-center justify-center font-bold"
                  style={{ background: 'var(--accent-red)', fontSize: '10px' }}>
                  {badge > 9 ? '9+' : badge}
                </span>
              )}
            </Link>
          ))}
        </div>

        {/* Auth */}
        <div className="hidden md:flex items-center gap-3">
          {isAuthenticated ? (
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-[var(--accent-red)] flex items-center justify-center text-sm font-bold">
                  {user?.first_name?.[0]?.toUpperCase() ?? 'U'}
                </div>
                <span className="text-sm text-[var(--text-primary)]">{user?.first_name}</span>
              </button>

              {dropdownOpen && (
                <div className="absolute right-0 mt-2 w-48 glass rounded-xl overflow-hidden shadow-xl">
                  <Link
                    to="/profile"
                    onClick={() => setDropdownOpen(false)}
                    className="flex items-center gap-3 px-4 py-3 text-sm hover:bg-white/5 transition-colors"
                  >
                    <User size={16} />
                    Mon profil
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm text-[var(--accent-red)] hover:bg-white/5 transition-colors"
                  >
                    <LogOut size={16} />
                    Déconnexion
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link to="/login" className="btn-secondary text-sm px-4 py-2">
                Connexion
              </Link>
              <Link to="/register" className="btn-primary text-sm px-4 py-2">
                S'inscrire
              </Link>
            </>
          )}
        </div>

        {/* Mobile burger */}
        <button
          className="md:hidden p-2 rounded-lg hover:bg-white/5"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          {menuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden glass border-t border-white/5 px-4 py-3 flex flex-col gap-2">
          {navLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              onClick={() => setMenuOpen(false)}
              className="px-4 py-2 rounded-lg text-sm font-medium text-[var(--text-muted)] hover:text-white hover:bg-white/5"
            >
              {label}
            </Link>
          ))}
          {isAuthenticated ? (
            <>
              <Link to="/profile" onClick={() => setMenuOpen(false)} className="px-4 py-2 text-sm">
                Mon profil
              </Link>
              <button onClick={handleLogout} className="px-4 py-2 text-sm text-[var(--accent-red)] text-left">
                Déconnexion
              </button>
            </>
          ) : (
            <Link to="/login" onClick={() => setMenuOpen(false)} className="btn-primary text-center text-sm">
              Connexion
            </Link>
          )}
        </div>
      )}
    </nav>
  )
}
