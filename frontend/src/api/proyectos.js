import client from './client'

export const getProyectos = (params) => client.get('/proyectos/', { params })
export const crearProyecto = (data) => client.post('/proyectos/', data)
export const actualizarProyecto = (id, data) => client.put(`/proyectos/${id}`, data)
export const eliminarProyecto = (id) => client.delete(`/proyectos/${id}`)
export const getItemsProyecto = (id) => client.get(`/proyectos/${id}/items`)