/**
 * Subida de fotos y videos (CU-47) -> POST /media/upload (exige sesión).
 * El backend acepta JPEG, PNG, WEBP y MP4 de hasta 25 MB y responde con la URL pública
 * desde la que sirve el archivo (/static/uploads/...).
 */
import { api } from '@/api/client'

const EXTENSIONES = {
  'image/jpeg': 'jpg',
  'image/png': 'png',
  'image/webp': 'webp',
  'video/mp4': 'mp4',
}

/**
 * Sube `archivo` (File o Blob) y devuelve su URL. Un Blob (p. ej. la foto de un reporte
 * guardado sin conexión) no trae nombre: se le pone uno según su tipo.
 */
export async function subirArchivo(archivo) {
  const nombre = archivo.name || `foto.${EXTENSIONES[archivo.type] ?? 'jpg'}`
  const formulario = new FormData()
  formulario.append('file', archivo, nombre)
  const { data } = await api.post('/media/upload', formulario)
  return data.url
}

/**
 * URL con la que el navegador carga un archivo subido. En desarrollo "/static/..." pasa por
 * el proxy de Vite; si la API está en otro dominio (VITE_API_URL absoluta), se usa ese dominio.
 */
export function urlPublica(url) {
  const base = import.meta.env.VITE_API_URL
  if (!url?.startsWith('/') || !base?.startsWith('http')) return url
  return new URL(url, base).href
}
