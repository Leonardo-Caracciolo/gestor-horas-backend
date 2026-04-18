import { createContext, useContext, useState, useEffect } from 'react'
import { login as loginApi } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user')
    return saved ? JSON.parse(saved) : null
  })

  const login = async (username, password) => {
    const res = await loginApi(username, password)
    const data = res.data
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data))
    setUser(data)
    return data
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  const hasPermiso = (clave) => user?.permisos?.includes(clave)

  return (
    <AuthContext.Provider value={{ user, login, logout, hasPermiso }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)