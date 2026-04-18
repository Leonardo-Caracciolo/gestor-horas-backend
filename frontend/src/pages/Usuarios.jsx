import { useState, useEffect } from 'react'
import client from '../api/client'

const ROLES_FIJOS = [
  { id: 1, nombre: 'Admin' },
]

const formVacio = {
  nombre: '',
  email: '',
  username: '',
  password: '',
  rol_id: '1',
}

// ── Helpers ──────────────────────────────────────────────────────────────

function parseError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map(d => {
        if (!d || typeof d !== 'object') return String(d)
        const campo = Array.isArray(d.loc) ? d.loc.filter(x => x !== 'body').join('.') : ''
        return campo ? `${campo}: ${d.msg || 'inválido'}` : (d.msg || 'inválido')
      })
      .join(' · ')
  }
  if (detail && typeof detail === 'object') return detail.msg || JSON.stringify(detail)
  return err?.message || 'Error'
}

// ── Componente ───────────────────────────────────────────────────────────

export default function Usuarios() {
  const [usuarios, setUsuarios] = useState([])
  const [loading, setLoading] = useState(true)
  const [errorCarga, setErrorCarga] = useState('')
  const [modalAbierto, setModalAbierto] = useState(false)
  const [form, setForm] = useState(formVacio)
  const [editandoId, setEditandoId] = useState(null)
  const [error, setError] = useState('')
  const [guardando, setGuardando] = useState(false)

  const cargar = async () => {
    try {
      setLoading(true)
      setErrorCarga('')
      const res = await client.get('/usuarios/')
      setUsuarios(Array.isArray(res.data) ? res.data : [])
    } catch (err) {
      setErrorCarga(parseError(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [])

  const handleNuevo = () => {
    setForm(formVacio)
    setEditandoId(null)
    setError('')
    setModalAbierto(true)
  }

  const handleEditar = (u) => {
    setForm({
      nombre: u.nombre || '',
      email: u.email || '',
      username: u.username || '',
      password: '',
      rol_id: String(u.rol_id ?? ''),
    })
    setEditandoId(u.id)
    setError('')
    setModalAbierto(true)
  }

  const handleDesactivar = async (id) => {
    if (!window.confirm('¿Desactivar este usuario?')) return
    try {
      await client.delete(`/usuarios/${id}`)
      cargar()
    } catch (err) {
      window.alert(parseError(err))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setGuardando(true)
    try {
      const payload = { ...form, rol_id: parseInt(form.rol_id) }
      if (editandoId) {
        delete payload.password
        delete payload.username  // username no se actualiza vía PUT
        await client.put(`/usuarios/${editandoId}`, payload)
      } else {
        await client.post('/usuarios/', payload)
      }
      setModalAbierto(false)
      cargar()
    } catch (err) {
      setError(parseError(err))
    } finally {
      setGuardando(false)
    }
  }

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  // Lookup de rol → string. Acepta tanto rol como objeto {id, nombre} como
  // string crudo (defensivo por si el backend cambia la forma).
  const nombreRol = (u) => {
    if (typeof u.rol === 'string') return u.rol
    if (u.rol && typeof u.rol === 'object') return u.rol.nombre || `#${u.rol.id}`
    const fijo = ROLES_FIJOS.find(r => r.id === u.rol_id)
    return fijo?.nombre || (u.rol_id != null ? `Rol #${u.rol_id}` : 'Sin rol')
  }

  if (loading) return <div className="text-gray-400 text-sm">Cargando...</div>
  if (errorCarga) return <div className="text-red-500 text-sm">{errorCarga}</div>

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Usuarios</h2>
          <p className="text-sm text-gray-400 mt-0.5">{usuarios.length} usuarios registrados</p>
        </div>
        <button
          onClick={handleNuevo}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          + Nuevo usuario
        </button>
      </div>

      <div className="space-y-2">
        {usuarios.map((u) => (
          <div
            key={u.id}
            className="bg-white rounded-lg border border-gray-100 px-4 py-3 flex items-center justify-between"
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                <span className="text-sm font-medium text-gray-800">{u.nombre}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-medium">
                  {nombreRol(u)}
                </span>
                {!u.activo && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-400">
                    Inactivo
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-400 truncate">
                {u.username} · {u.email}
              </p>
            </div>
            <div className="flex items-center gap-3 ml-4 shrink-0">
              <button
                onClick={() => handleEditar(u)}
                className="text-xs text-blue-600 hover:underline"
              >
                Editar
              </button>
              {u.activo && (
                <button
                  onClick={() => handleDesactivar(u.id)}
                  className="text-xs text-red-500 hover:underline"
                >
                  Desactivar
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {modalAbierto && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-base font-bold text-gray-800">
                {editandoId ? 'Editar usuario' : 'Nuevo usuario'}
              </h3>
              <button
                onClick={() => setModalAbierto(false)}
                className="text-gray-400 hover:text-gray-600 text-xl leading-none"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre completo
                </label>
                <input
                  type="text"
                  name="nombre"
                  value={form.nombre}
                  onChange={handleChange}
                  required
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  required
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Usuario</label>
                <input
                  type="text"
                  name="username"
                  value={form.username}
                  onChange={handleChange}
                  required
                  disabled={!!editandoId}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
                />
              </div>
              {!editandoId && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contraseña
                  </label>
                  <input
                    type="password"
                    name="password"
                    value={form.password}
                    onChange={handleChange}
                    required
                    minLength={8}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
                <select
                  name="rol_id"
                  value={form.rol_id}
                  onChange={handleChange}
                  required
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {ROLES_FIJOS.map(r => (
                    <option key={r.id} value={r.id}>{r.nombre}</option>
                  ))}
                </select>
              </div>

              {error && (
                <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 whitespace-pre-wrap">
                  {error}
                </p>
              )}

              <div className="flex gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => setModalAbierto(false)}
                  className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={guardando}
                  className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 rounded-lg transition-colors"
                >
                  {guardando ? 'Guardando...' : editandoId ? 'Guardar cambios' : 'Crear'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}