/**
 * Donaciones y emparejamiento (M11 · aid). Conectado al backend real:
 *  - CU-33 Ofrecer ayuda          -> POST /aid/offers
 *  - CU-33 Mis ofertas            -> GET  /aid/offers/mine
 *  - CU-42 Necesidades pendientes -> GET  /aid/needs/pending (admin)
 *  - CU-41 Ofertas disponibles    -> GET  /aid/offers/pending (admin)
 *  - CU-42 Ejecutar emparejamiento -> POST /aid/matching/run (admin)
 * El emparejamiento cruza misma categoría y unidad, a 15 km como máximo, empezando por la
 * necesidad más urgente; lo que sobra de una oferta sigue disponible.
 */
import { api } from '@/api/client'

/** Categorías (AidCategory del backend). */
export const CATEGORIAS_AYUDA = {
  ALIMENTOS: 'Alimentos',
  AGUA: 'Agua',
  HERRAMIENTAS: 'Herramientas',
  REFUGIO: 'Refugio',
  ROPA: 'Ropa',
  PRIMEROS_AUXILIOS: 'Primeros auxilios',
  OTROS: 'Otros',
}

export const PRIORIDADES = {
  BAJA: 'Baja',
  MEDIA: 'Media',
  ALTA: 'Alta',
  URGENTE: 'Urgente',
}

/** Estados de ofertas y necesidades (AidStatus del backend). */
export const ESTADOS_AYUDA = {
  PENDIENTE: 'Disponible',
  EMPAREJADO: 'Emparejada',
  ENTREGADO: 'Entregada',
  CANCELADO: 'Cancelada',
}

/** `ubicacion` es [lat, lng]. */
export async function ofrecerAyuda({ titulo, categoria, cantidad, unidad, ubicacion }) {
  const { data } = await api.post('/aid/offers', {
    title: titulo.trim(),
    category: categoria,
    quantity: Number(cantidad),
    unit: unidad.trim(),
    latitude: ubicacion[0],
    longitude: ubicacion[1],
  })
  return data
}

export async function listarMisOfertas() {
  const { data } = await api.get('/aid/offers/mine')
  return data
}

export async function listarNecesidadesPendientes() {
  const { data } = await api.get('/aid/needs/pending')
  return data
}

export async function listarOfertasPendientes() {
  const { data } = await api.get('/aid/offers/pending')
  return data
}

/** Devuelve los emparejamientos creados en esta corrida (puede ser una lista vacía). */
export async function ejecutarEmparejamiento() {
  const { data } = await api.post('/aid/matching/run')
  return data
}

/** Cantidad con la unidad, sin decimales innecesarios: 12.5 kg, 3 litros. */
export function formatearCantidad(cantidad, unidad) {
  return `${Number(cantidad).toLocaleString('es-CO', { maximumFractionDigits: 2 })} ${unidad}`
}
