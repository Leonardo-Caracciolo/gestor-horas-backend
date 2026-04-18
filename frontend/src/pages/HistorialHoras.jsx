import { useState, useEffect, useMemo } from 'react'
import { getMisHoras, eliminarHora } from '../api/horas'
import { getProyectos, getItemsProyecto } from '../api/proyectos'

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

function formatearFecha(iso) {
  const [y, m, d] = iso.split('-').map(Number)
  return `${String(d).padStart(2, '0')}/${String(m).padStart(2, '0')}/${y}`
}

const ESTADOS = ['Borrador', 'Enviado', 'Aprobado', 'Rechazado']

function badgeEstado(estado) {
  const base = 'text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded font-medium'
  const map = {
    Aprobado:  `${base} bg-green-50 text-green-700`,
    Borrador:  `${base} bg-gray-100 text-gray-600`,
    Enviado:   `${base} bg-blue-50 text-blue-700`,
    Rechazado: `${base} bg-red-50 text-red-700`,
  }
  return map[estado] || `${base} bg-gray-100 text-gray-600`
}

// Default: mes actual completo (1° del mes a hoy)
function fechasDefault() {
  const hoy = new Date()
  const desde = new Date(hoy.getFullYear(), hoy.getMonth(), 1)
  const iso = (d) => d.toISOString().split('T')[0]
  return { fecha_desde: iso(desde), fecha_hasta: iso(hoy) }
}

// ── Componente ───────────────────────────────────────────────────────────

export default function HistorialHoras() {
  const [registros, setRegistros] = useState([])
  const [proyectos, setProyectos] = useState([])
  const [itemsAdo, setItemsAdo] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [filtros, setFiltros] = useState({ ...fechasDefault(), estado: '' })
  const [orden, setOrden] = useState({ campo: 'fecha', dir: 'desc' })

  const proyectosById = useMemo(() => {
    const m = new Map()
    for (const p of proyectos) m.set(p.id, p)
    return m
  }, [proyectos])

  const itemsById = useMemo(() => {
    const m = new Map()
    for (const i of itemsAdo) m.set(i.id, i)
    return m
  }, [itemsAdo])

  const cargar = async () => {
    try {
      setLoading(true)
      setError('')
      const params = {}
      if (filtros.fecha_desde) params.fecha_desde = filtros.fecha_desde
      if (filtros.fecha_hasta) params.fecha_hasta = filtros.fecha_hasta
      if (filtros.estado) params.estado = filtros.estado

      const res = await getMisHoras(params)
      setRegistros(Array.isArray(res.data) ? res.data : [])

      // Catálogos en paralelo, no bloqueantes
      getProyectos()
        .then(r => setProyectos(Array.isArray(r.data) ? r.data : []))
        .catch(() => {})
      getItemsProyecto(2)
        .then(r => setItemsAdo(Array.isArray(r.data) ? r.data : []))
        .catch(() => {})
    } catch (err) {
      setError(parseError(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, []) // eslint-disable-line

  const handleAplicarFiltros = (e) => {
    e.preventDefault()
    cargar()
  }

  const handleLimpiarFiltros = () => {
    setFiltros({ ...fechasDefault(), estado: '' })
    setTimeout(cargar, 0)
  }

  const handleEliminar = async (id) => {
    if (!window.confirm('¿Eliminar este registro?')) return
    try {
      await eliminarHora(id)
      cargar()
    } catch (err) {
      window.alert(parseError(err))
    }
  }

  // Datos enriquecidos con nombres legibles
  const filas = useMemo(() => {
    return registros.map(r => {
      const proy = proyectosById.get(r.proyecto_id)
      let tareaTxt = ''
      if (r.es_ceremonia) tareaTxt = 'Ceremonia'
      else if (r.tarea_manual) tareaTxt = r.tarea_manual
      else if (r.ado_task_id) {
        const it = itemsById.get(r.ado_task_id)
        tareaTxt = it ? `[${it.ado_id}] ${it.titulo}` : `Tarea #${r.ado_task_id}`
      }
      return {
        ...r,
        _proyecto: proy?.nombre || `Proyecto #${r.proyecto_id}`,
        _tarea: tareaTxt,
        _horasNum: parseFloat(r.horas || 0),
      }
    })
  }, [registros, proyectosById, itemsById])

  // Ordenamiento
  const filasOrdenadas = useMemo(() => {
    const arr = [...filas]
    const { campo, dir } = orden
    arr.sort((a, b) => {
      let va = a[campo], vb = b[campo]
      if (campo === 'horas') { va = a._horasNum; vb = b._horasNum }
      if (va == null) va = ''
      if (vb == null) vb = ''
      if (va < vb) return dir === 'asc' ? -1 : 1
      if (va > vb) return dir === 'asc' ? 1 : -1
      return 0
    })
    return arr
  }, [filas, orden])

  const totalHoras = useMemo(
    () => filas.reduce((acc, r) => acc + r._horasNum, 0),
    [filas]
  )

  const cambiarOrden = (campo) => {
    setOrden(o =>
      o.campo === campo
        ? { campo, dir: o.dir === 'asc' ? 'desc' : 'asc' }
        : { campo, dir: 'asc' }
    )
  }

  const flecha = (campo) => {
    if (orden.campo !== campo) return ''
    return orden.dir === 'asc' ? ' ↑' : ' ↓'
  }

  return (
    <div className="max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Historial de Horas</h2>
          <p className="text-sm text-gray-400 mt-0.5">
            {filas.length} registros · Total: {totalHoras.toFixed(2)}h
          </p>
        </div>
      </div>

      {/* Filtros */}
      <form
        onSubmit={handleAplicarFiltros}
        className="bg-white rounded-lg border border-gray-100 p-4 mb-4 flex items-end gap-3 flex-wrap"
      >
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Desde</label>
          <input
            type="date"
            value={filtros.fecha_desde}
            onChange={e => setFiltros({ ...filtros, fecha_desde: e.target.value })}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Hasta</label>
          <input
            type="date"
            value={filtros.fecha_hasta}
            onChange={e => setFiltros({ ...filtros, fecha_hasta: e.target.value })}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Estado</label>
          <select
            value={filtros.estado}
            onChange={e => setFiltros({ ...filtros, estado: e.target.value })}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos</option>
            {ESTADOS.map(e => <option key={e} value={e}>{e}</option>)}
          </select>
        </div>
        <button
          type="submit"
          className="px-4 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          Aplicar
        </button>
        <button
          type="button"
          onClick={handleLimpiarFiltros}
          className="px-4 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
        >
          Limpiar
        </button>
      </form>

      {/* Estados */}
      {loading && <div className="text-gray-400 text-sm">Cargando...</div>}
      {error && <div className="text-red-500 text-sm mb-3">{error}</div>}

      {/* Tabla */}
      {!loading && !error && (
        <div className="bg-white rounded-lg border border-gray-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th
                    className="px-3 py-2 text-left cursor-pointer hover:text-gray-700"
                    onClick={() => cambiarOrden('fecha')}
                  >
                    Fecha{flecha('fecha')}
                  </th>
                  <th
                    className="px-3 py-2 text-left cursor-pointer hover:text-gray-700"
                    onClick={() => cambiarOrden('_proyecto')}
                  >
                    Proyecto{flecha('_proyecto')}
                  </th>
                  <th className="px-3 py-2 text-left">Tarea</th>
                  <th className="px-3 py-2 text-left">Descripción</th>
                  <th
                    className="px-3 py-2 text-right cursor-pointer hover:text-gray-700"
                    onClick={() => cambiarOrden('horas')}
                  >
                    Horas{flecha('horas')}
                  </th>
                  <th
                    className="px-3 py-2 text-left cursor-pointer hover:text-gray-700"
                    onClick={() => cambiarOrden('estado')}
                  >
                    Estado{flecha('estado')}
                  </th>
                  <th className="px-3 py-2 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filasOrdenadas.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-3 py-6 text-center text-gray-400">
                      No hay registros para los filtros seleccionados.
                    </td>
                  </tr>
                ) : (
                  filasOrdenadas.map(r => (
                    <tr key={r.id} className="border-t border-gray-100 hover:bg-gray-50">
                      <td className="px-3 py-2 whitespace-nowrap text-gray-700">
                        {formatearFecha(r.fecha)}
                      </td>
                      <td className="px-3 py-2 text-gray-700">{r._proyecto}</td>
                      <td className="px-3 py-2 text-gray-500 max-w-xs truncate" title={r._tarea}>
                        {r._tarea || '—'}
                      </td>
                      <td className="px-3 py-2 text-gray-700 max-w-md truncate" title={r.descripcion}>
                        {r.descripcion}
                      </td>
                      <td className="px-3 py-2 text-right font-medium text-gray-800 whitespace-nowrap">
                        {r._horasNum.toFixed(2)}
                      </td>
                      <td className="px-3 py-2">
                        <span className={badgeEstado(r.estado)}>{r.estado}</span>
                      </td>
                      <td className="px-3 py-2 text-right whitespace-nowrap">
                        {r.estado === 'Borrador' && (
                          <button
                            onClick={() => handleEliminar(r.id)}
                            className="text-xs text-red-500 hover:underline"
                          >
                            Eliminar
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
              {filasOrdenadas.length > 0 && (
                <tfoot className="bg-gray-50 text-sm font-semibold">
                  <tr>
                    <td colSpan={4} className="px-3 py-2 text-right text-gray-600">Total</td>
                    <td className="px-3 py-2 text-right text-gray-800">{totalHoras.toFixed(2)}</td>
                    <td colSpan={2}></td>
                  </tr>
                </tfoot>
              )}
            </table>
          </div>
        </div>
      )}
    </div>
  )
}