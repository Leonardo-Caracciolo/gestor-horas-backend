import { useState, useEffect } from 'react'
import { crearHora } from '../api/horas'
import { getItemsProyecto } from '../api/proyectos'

const PROYECTO_OFICINA_ID = 1
const PROYECTO_BPS_ID = 2

function parseError(err) {
  const detail = err?.response?.data?.detail
  if (!detail) return 'Error al guardar'
  if (Array.isArray(detail)) return detail.map(d => d.msg || JSON.stringify(d)).join(', ')
  if (typeof detail === 'string') return detail
  return 'Error al guardar'
}

export default function FormularioHora({ onCerrar }) {
  const [tipo, setTipo] = useState('PROYECTO')
  const [todosItems, setTodosItems] = useState([])
  const [epicSel, setEpicSel] = useState('')
  const [featureSel, setFeatureSel] = useState('')
  const [itemSel, setItemSel] = useState('')
  const [form, setForm] = useState({
    fecha: new Date().toISOString().split('T')[0],
    descripcion: '',
    horas: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (tipo === 'PROYECTO') {
      getItemsProyecto(PROYECTO_BPS_ID).then(res => setTodosItems(res.data)).catch(() => {})
    }
  }, [tipo])

  const epics = todosItems.filter(i => i.tipo === 'Epic')
  const epicSelObj = epics.find(e => String(e.id) === epicSel)
  const features = epicSelObj
    ? todosItems.filter(i => i.tipo === 'Feature' && i.parent_id === epicSelObj.id)
    : []
  const featureSelObj = features.find(f => String(f.id) === featureSel)
  const tasks = featureSelObj
    ? todosItems.filter(i => (i.tipo === 'Task' || i.tipo === 'User Story') && i.parent_id === featureSelObj.id)
    : []

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await crearHora({
        fecha: form.fecha,
        descripcion: form.descripcion,
        horas: parseFloat(form.horas),
        proyecto_id: tipo === 'OFICINA' ? PROYECTO_OFICINA_ID : PROYECTO_BPS_ID,
        ado_task_id: itemSel ? parseInt(itemSel) : null,
        es_ceremonia: false,
      })
      onCerrar()
    } catch (err) {
      setError(parseError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-base font-bold text-gray-800">Cargar horas</h3>
          <button onClick={onCerrar} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tipo</label>
            <div className="flex gap-2">
              {['PROYECTO', 'OFICINA'].map(t => (
                <button key={t} type="button"
                  onClick={() => { setTipo(t); setEpicSel(''); setFeatureSel(''); setItemSel('') }}
                  className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                    tipo === t ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >{t}</button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fecha</label>
            <input type="date" value={form.fecha}
              onChange={e => setForm({ ...form, fecha: e.target.value })} required
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          {tipo === 'PROYECTO' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Epica ({epics.length})</label>
                <select value={epicSel}
                  onChange={e => { setEpicSel(e.target.value); setFeatureSel(''); setItemSel('') }}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="">Selecciona una epica</option>
                  {epics.map(e => <option key={e.id} value={e.id}>[{e.ado_id}] {e.titulo}</option>)}
                </select>
              </div>

              {epicSel && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Feature ({features.length})</label>
                  <select value={featureSel}
                    onChange={e => { setFeatureSel(e.target.value); setItemSel('') }}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">Selecciona una feature</option>
                    {features.map(f => <option key={f.id} value={f.id}>[{f.ado_id}] {f.titulo}</option>)}
                  </select>
                </div>
              )}

              {featureSel && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tarea / User Story ({tasks.length})</label>
                  <select value={itemSel} onChange={e => setItemSel(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">Selecciona una tarea</option>
                    {tasks.map(t => <option key={t.id} value={t.id}>[{t.ado_id}] {t.titulo}</option>)}
                  </select>
                </div>
              )}
            </>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Descripcion</label>
            <textarea value={form.descripcion}
              onChange={e => setForm({ ...form, descripcion: e.target.value })}
              required rows={3} placeholder="Que hiciste?"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Horas</label>
            <input type="number" value={form.horas}
              onChange={e => setForm({ ...form, horas: e.target.value })}
              required min="0.25" max="12" step="0.25" placeholder="0.00"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          {error && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}

          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onCerrar}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
              Cancelar
            </button>
            <button type="submit" disabled={loading}
              className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 rounded-lg transition-colors">
              {loading ? 'Guardando...' : 'Cargar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}