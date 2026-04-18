import { useState, useEffect } from 'react'
import { getResumenSemana, eliminarHora } from '../api/horas'
import FormularioHora from '../components/FormularioHora'

export default function MisHoras() {
  const [resumen, setResumen] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modalAbierto, setModalAbierto] = useState(false)

  const cargarResumen = async () => {
    try {
      setLoading(true)
      setError('')
      const res = await getResumenSemana()
      setResumen(res.data)
    } catch (err) {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        setError('Error al cargar las horas')
      } else {
        setError(detail || 'Error al cargar las horas')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargarResumen() }, [])

  const handleEliminar = async (id) => {
    if (!confirm('Eliminar este registro?')) return
    try {
      await eliminarHora(id)
      cargarResumen()
    } catch (err) {
      const detail = err.response?.data?.detail
      alert(Array.isArray(detail) ? 'Error al eliminar' : detail || 'Error al eliminar')
    }
  }

  if (loading) return <div className="text-gray-400 text-sm">Cargando...</div>
  if (error) return <div className="text-red-500 text-sm">{error}</div>

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Mis Horas</h2>
          <p className="text-sm text-gray-400 mt-0.5">Semana actual</p>
        </div>
        <button
          onClick={() => setModalAbierto(true)}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          + Cargar horas
        </button>
      </div>

      {resumen?.dias?.map((dia) => (
        <div key={dia.fecha} className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
              {dia.nombre_dia} {dia.fecha}
            </h3>
            <span className="text-sm font-medium text-gray-700">{dia.total_horas}h</span>
          </div>

          {dia.registros?.length === 0 ? (
            <div className="bg-white rounded-lg border border-dashed border-gray-200 px-4 py-3 text-sm text-gray-400">
              Sin registros
            </div>
          ) : (
            <div className="space-y-2">
              {dia.registros.map((r) => (
                <div key={r.id} className="bg-white rounded-lg border border-gray-100 px-4 py-3 flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{r.descripcion}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {r.proyecto_nombre}
                      {r.tarea_manual ? ` · ${r.tarea_manual}` : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 ml-4">
                    <span className="text-sm font-semibold text-gray-700">{r.horas}h</span>
                    <button
                      onClick={() => handleEliminar(r.id)}
                      className="text-xs text-red-500 hover:underline"
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}

      {resumen?.total_semana !== undefined && (
        <div className="mt-4 pt-4 border-t border-gray-200 flex justify-end">
          <span className="text-sm font-semibold text-gray-700">
            Total semana: {resumen.total_semana}h
          </span>
        </div>
      )}

      {modalAbierto && (
        <FormularioHora
          onCerrar={() => { setModalAbierto(false); cargarResumen() }}
        />
      )}
    </div>
  )
}