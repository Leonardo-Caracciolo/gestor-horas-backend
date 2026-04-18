import { useState, useEffect } from 'react'
import { getProyectos, crearProyecto, actualizarProyecto, eliminarProyecto } from '../api/proyectos'

const TIPOS = ['PROYECTO', 'OFICINA']

const formVacio = {
  nombre: '',
  tipo: 'PROYECTO',
  id_proyecto_excel: '',
  ado_project_name: '',
  descripcion: '',
}

export default function Proyectos() {
  const [proyectos, setProyectos] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalAbierto, setModalAbierto] = useState(false)
  const [form, setForm] = useState(formVacio)
  const [editandoId, setEditandoId] = useState(null)
  const [error, setError] = useState('')
  const [guardando, setGuardando] = useState(false)

  const cargar = async () => {
    try {
      setLoading(true)
      const res = await getProyectos()
      setProyectos(res.data)
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

  const handleEditar = (p) => {
    setForm({
      nombre: p.nombre,
      tipo: p.tipo,
      id_proyecto_excel: p.id_proyecto_excel,
      ado_project_name: p.ado_project_name || '',
      descripcion: p.descripcion || '',
    })
    setEditandoId(p.id)
    setError('')
    setModalAbierto(true)
  }

  const handleEliminar = async (id) => {
    if (!confirm('¿Desactivar este proyecto?')) return
    try {
      await eliminarProyecto(id)
      cargar()
    } catch (err) {
      alert(err.response?.data?.detail || 'Error al eliminar')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setGuardando(true)
    try {
      if (editandoId) {
        await actualizarProyecto(editandoId, form)
      } else {
        await crearProyecto(form)
      }
      setModalAbierto(false)
      cargar()
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al guardar')
    } finally {
      setGuardando(false)
    }
  }

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  if (loading) return <div className="text-gray-400 text-sm">Cargando...</div>

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Proyectos</h2>
          <p className="text-sm text-gray-400 mt-0.5">{proyectos.length} proyectos registrados</p>
        </div>
        <button
          onClick={handleNuevo}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          + Nuevo proyecto
        </button>
      </div>

      <div className="space-y-2">
        {proyectos.map((p) => (
          <div key={p.id} className="bg-white rounded-lg border border-gray-100 px-4 py-3 flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-sm font-medium text-gray-800">{p.nombre}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  p.tipo === 'PROYECTO' ? 'bg-blue-50 text-blue-700' : 'bg-purple-50 text-purple-700'
                }`}>
                  {p.tipo}
                </span>
                {!p.activo && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-400">Inactivo</span>
                )}
              </div>
              <p className="text-xs text-gray-400">
                ID Excel: {p.id_proyecto_excel}
                {p.ado_project_name ? ` · ADO: ${p.ado_project_name}` : ''}
              </p>
            </div>
            <div className="flex items-center gap-3 ml-4">
              <button onClick={() => handleEditar(p)} className="text-xs text-blue-600 hover:underline">Editar</button>
              {p.activo && (
                <button onClick={() => handleEliminar(p.id)} className="text-xs text-red-500 hover:underline">Desactivar</button>
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
                {editandoId ? 'Editar proyecto' : 'Nuevo proyecto'}
              </h3>
              <button onClick={() => setModalAbierto(false)} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                <select
                  name="tipo"
                  value={form.tipo}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {TIPOS.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ID Proyecto Excel</label>
                <input
                  type="text"
                  name="id_proyecto_excel"
                  value={form.id_proyecto_excel}
                  onChange={handleChange}
                  required
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Ej: PROJ-001"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Proyecto ADO (opcional)</label>
                <input
                  type="text"
                  name="ado_project_name"
                  value={form.ado_project_name}
                  onChange={handleChange}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Nombre exacto en Azure DevOps"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descripción (opcional)</label>
                <textarea
                  name="descripcion"
                  value={form.descripcion}
                  onChange={handleChange}
                  rows={2}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                />
              </div>

              {error && (
                <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
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