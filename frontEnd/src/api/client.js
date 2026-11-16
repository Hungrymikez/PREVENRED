import axios from 'axios'

export const TOKEN_KEY = 'prevenred_token'

/** Cliente HTTP único para toda la app. Agrega el token de sesión a cada petición. */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

/**
 * Convierte cualquier error de la API en un mensaje legible.
 * El backend responde de dos formas:
 *  - Errores de negocio: {"error": {"code": "...", "message": "..."}}
 *  - Errores de validación de FastAPI (422): {"detail": [{"msg": "...", "loc": [...]}]}
 */
export function mensajeDeError(error) {
  const data = error?.response?.data
  if (data?.error?.message) return data.error.message
  if (Array.isArray(data?.detail)) return data.detail.map((d) => d.msg).join('. ')
  if (typeof data?.detail === 'string') return data.detail
  if (!error?.response) return 'No hay conexión con el servidor. Intenta de nuevo.'
  // Sin mensaje del servidor: uno claro según el tipo de error (nunca el texto técnico).
  const estado = error.response.status
  if (estado === 401) return 'Tu sesión terminó. Vuelve a iniciar sesión.'
  if (estado === 403) return 'Tu tipo de cuenta no tiene permiso para ver o hacer esto.'
  if (estado === 404) return 'No encontramos lo que buscas.'
  if (estado >= 500) return 'El servidor tuvo un problema. Intenta de nuevo en unos minutos.'
  return 'Ocurrió un error inesperado.'
}

/**
 * Texto para mostrar de cualquier error: los de la API se traducen con mensajeDeError;
 * los errores propios de la app (new Error('…')) ya traen un mensaje pensado para la persona.
 */
export function textoDeError(error) {
  if (error?.response || error?.isAxiosError || error?.message === 'Network Error') {
    return mensajeDeError(error)
  }
  return error?.message || mensajeDeError(error)
}
