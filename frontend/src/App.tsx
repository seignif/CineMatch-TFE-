import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

// Pages (à créer progressivement lors des sprints suivants)
const Placeholder = ({ name }: { name: string }) => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="text-center">
      <h1 className="text-3xl font-bold text-primary mb-2">CineMatch</h1>
      <p className="text-gray-400">Page : {name}</p>
      <p className="text-sm text-gray-600 mt-4">Sprint 0 - Setup complet ✓</p>
    </div>
  </div>
)

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/films" replace />} />
        <Route path="/login" element={<Placeholder name="Login" />} />
        <Route path="/register" element={<Placeholder name="Register" />} />
        <Route path="/films" element={<Placeholder name="Films" />} />
        <Route path="/films/:id" element={<Placeholder name="FilmDetail" />} />
        <Route path="/matching" element={<Placeholder name="Matching" />} />
        <Route path="/matches" element={<Placeholder name="Matches" />} />
        <Route path="/chat" element={<Placeholder name="Chat" />} />
        <Route path="/profile" element={<Placeholder name="Profile" />} />
        <Route path="/outings" element={<Placeholder name="PlannedOutings" />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
