import { useState, useEffect, useMemo } from 'react'
import { getResumenSemana, eliminarHora } from '../api/horas'
import { getProyectos, getItemsProyecto } from '../api/proyectos'
import FormularioHora from '../components/FormularioHora'

// ── Helpers ──────────────────────────────────────────────────────────────

const DIAS_ES = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']

/** "2026-04-14" → "Martes 14/04" (sin sumar zona horaria que corra el día). */
function formatearDia(iso) {
  const [y, m, d] = iso.split('-').map(Number)
  const dt = new Date(y, m - 1, d)
  const nombre = DIAS_ES[dt.getDay()]
  const dd = String(d).padStart(2, '0')
  const mm = String(m).padStart(2, '0')
  return { nombre, corto: `${dd}/${mm}` }
}

/** Convierte el detail de un error (string | array Pydantic | object) a string. */
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
  return err?.message || 'Error al cargar'
}

/** Suma Decimales que vienen como string desde el backend. */
function sumarHoras(registros) {
  return registros.reduce((acc, r) => acc + parseFloat(r.horas || 0), 0)
}

/** Formatea un número a N hs con 2 decimales. */
const fmtHoras = (n) => `${Number(n).toFixed(2)}h`

// ── Componente ───────────────────────────────────────────────────────────

export default function MisHoras() {
  const [dias, setDias] = useState([])           // list[ResumenDiario] tal cual llega
  const [proyectos, setProyectos] = useState([]) // catálogo para lookup por id
  const [itemsAdo, setItemsAdo] = useState([])   // catálogo para lookup por id
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modalAbierto, setModalAbierto] = useState(false)

  // Lookups memorizados: id → nombre
  const proyectosById = useMemo(() => {
    const map = new Map()
    for (const p of proyectos) map.set(p.id, p)
    return map
  }, [proyectos])

  const itemsById = useMemo(() => {
    const map = new Map()
    for (const i of itemsAdo) map.set(i.id, i)
    return map
  }, [itemsAdo])

  const totalSemana = useMemo(
    () => dias.reduce((acc, d) => acc + parseFloat(d.total_horas || 0), 0),
    [dias]
  )

  const cargarTodo = async () => {
    try {
      setLoading(true)
      setError('')

      // 1) El dato crítico: resumen semanal
      const resSemana = await getResumenSemana()
      setDias(Array.isArray(resSemana.data) ? resSemana.data : [])

      // 2) Catálogos (no bloqueantes: si fallan, mostramos sin nombres)
      getProyectos()
        .then(r => setProyectos(Array.isArray(r.data) ? r.data : []))
        .catch(() => {})

      // Para los items solo traemos los del proyecto BPS (id 2). OFICINA no tiene ítems ADO.
      getItemsProyecto(2)
        .then(r => setItemsAdo(Array.isArray(r.data) ? r.data : []))
        .catch(() => {})
    } catch (err) {
      setError(parseError(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargarTodo() }, [])

  const handleEliminar = async (id) => {
    if (!window.confirm('¿Eliminar este registro?')) return
    try {
      await eliminarHora(id)
      cargarTodo()
    } catch (err) {
      window.alert(parseError(err))
    }
  }

  const renderTareaSubtitulo = (r) => {
    const proy = proyectosById.get(r.proyecto_id)
    const nombreProy = proy?.nombre || `Proyecto #${r.proyecto_id}`

    if (r.es_ceremonia) return `${nombreProy} · Ceremonia`
    if (r.tarea_manual) return `${nombreProy} · ${r.tarea_manual}`
    if (r.ado_task_id) {
      const item = itemsById.get(r.ado_task_id)
      if (item) return `${nombreProy} · [${item.ado_id}] ${item.titulo}`
      return `${nombreProy} · Tarea #${r.ado_task_id}`
    }
    return nombreProy
  }

  const badgeEstado = (estado) => {
    const base = 'text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded font-medium'
    switch (estado) {
      case 'Aprobado':  return `${base} bg-green-50 text-green-700`
      case 'Borrador':  return `${base} bg-gray-100 text-gray-600`
      case 'Enviado':   return `${base} bg-blue-50 text-blue-700`
      case 'Rechazado': return `${base} bg-red-50 text-red-700`
      default:          return `${base} bg-gray-100 text-gray-600`
    }
  }

  if (loading) return <div className="text-gray-400 text-sm">Cargando...</div>
  if (error)   return <div className="text-red-500 text-sm">{error}</div>

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

      {dias.length === 0 && (
        <div className="bg-white rounded-lg border border-dashed border-gray-200 px-4 py-6 text-sm text-gray-400 text-center">
          No hay datos para esta semana.
        </div>
      )}

      {dias.map((dia) => {
        const { nombre, corto } = formatearDia(dia.fecha)
        const registros = dia.registros || []
        return (
          <div key={dia.fecha} className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
                {nombre} {corto}
              </h3>
              <span className="text-sm font-medium text-gray-700">
                {fmtHoras(dia.total_horas)}
              </span>
            </div>

            {registros.length === 0 ? (
              <div className="bg-white rounded-lg border border-dashed border-gray-200 px-4 py-3 text-sm text-gray-400">
                Sin registros
              </div>
            ) : (
              <div className="space-y-2">
                {registros.map((r) => (
                  <div
                    key={r.id}
                    className="bg-white rounded-lg border border-gray-100 px-4 py-3 flex items-center justify-between"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-gray-800 truncate">
                          {r.descripcion}
                        </p>
                        <span className={badgeEstado(r.estado)}>{r.estado}</span>
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5 truncate">
                        {renderTareaSubtitulo(r)}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 ml-4 shrink-0">
                      <span className="text-sm font-semibold text-gray-700">
                        {fmtHoras(r.horas)}
                      </span>
                      {r.estado === 'Borrador' && (
                        <button
                          onClick={() => handleEliminar(r.id)}
                          className="text-xs text-red-500 hover:underline"
                        >
                          Eliminar
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}

      {dias.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200 flex justify-end">
          <span className="text-sm font-semibold text-gray-700">
            Total semana: {fmtHoras(totalSemana)}
          </span>
        </div>
      )}

      {modalAbierto && (
        <FormularioHora
          onCerrar={() => {
            setModalAbierto(false)
            cargarTodo()
          }}
        />
      )}
    </div>
  )
}