import client from './client'

export const getMisHoras = (params) => client.get('/horas/', { params })
export const getResumenSemana = () => client.get('/horas/semana')
export const crearHora = (data) => client.post('/horas/', data)
export const actualizarHora = (id, data) => client.put(`/horas/${id}`, data)
export const eliminarHora = (id) => client.delete(`/horas/${id}`)
export const enviarSemana = () => client.post('/horas/enviar')
export const iniciarTimer = (data) => client.post('/horas/timer/iniciar', data)
export const detenerTimer = (id) => client.post(`/horas/${id}/timer/detener`)