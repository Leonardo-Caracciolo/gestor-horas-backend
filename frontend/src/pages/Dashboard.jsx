import { Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import MisHoras from './MisHoras'
import Usuarios from './Usuarios'

export default function Dashboard() {
  const { user, logout, hasPermiso } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-5 py-5 border-b border-gray-100">
          <h1 className="text-base font-bold text-gray-800">Gestor de Horas</h1>
          <p className="text-xs text-gray-400 mt-0.5">v1.0.0</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            Mis Horas
          </NavLink>

          {hasPermiso('admin_usuarios') && (
            <NavLink
              to="/usuarios"
              className={({ isActive }) =>
                `block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
                }`
              }
            >
              Usuarios
            </NavLink>
          )}
        </nav>

        <div className="px-3 py-4 border-t border-gray-100">
          <div className="px-3 py-2 mb-2">
            <p className="text-sm font-medium text-gray-700">{user?.nombre}</p>
            <p className="text-xs text-gray-400">{user?.rol}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-full text-left px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50 transition-colors"
          >
            Cerrar sesion
          </button>
        </div>
      </aside>

      <main className="flex-1 p-8 overflow-auto">
        <Routes>
          <Route path="/" element={<MisHoras />} />
          <Route path="/usuarios" element={<Usuarios />} />
        </Routes>
      </main>
    </div>
  )
}
