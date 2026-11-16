/**
 * OficiosYa (contexto `services` del backend, prefijo /services/technicians).
 * - CU-17 Registrar perfil técnico: obtenerMiPerfil, guardarMiPerfil
 * - CU-18 Verificar técnico (Administrador): listarPendientes, verificarTecnico
 * - CU-19 Buscar servicios técnicos: listarTecnicos, obtenerTecnico
 * - CU-22 Contactar por WhatsApp: enlaceWhatsapp
 */
import { api } from '@/api/client'
import { CENTRO_PEREIRA } from '@/utils/mapa'
import { ZONAS } from '@/utils/zonas'

const BASE = '/services/technicians'

/** Enum `Specialty` del backend con su nombre para mostrar. */
export const ESPECIALIDADES = {
  PLOMERIA: 'Plomería',
  ELECTRICIDAD: 'Electricidad',
  CONSTRUCCION: 'Construcción',
  CARPINTERIA: 'Carpintería',
  PINTURA: 'Pintura',
  CERRAJERIA: 'Cerrajería',
  OTRO: 'Otro',
}

/** Enum `VerificationStatus` del backend. */
export const ESTADOS_VERIFICACION = {
  PENDIENTE: 'Pendiente de verificación',
  VERIFICADO: 'Verificado',
  RECHAZADO: 'Rechazado',
}

/** Radio de búsqueda: un barrio y sus alrededores, o toda Pereira. */
const RADIO_ZONA_METROS = 3000
const RADIO_CIUDAD_METROS = 15000

export function nombreEspecialidad(codigo) {
  return ESPECIALIDADES[codigo] ?? codigo
}

/**
 * Barrio de referencia más cercano a un punto. El backend guarda coordenadas, no el barrio:
 * se deriva para mostrar una ubicación aproximada (RN-05).
 */
export function zonaCercana([lat, lng]) {
  let mejor = ZONAS[0]
  let menor = Infinity
  for (const zona of ZONAS) {
    const d = (zona.coordenadas[0] - lat) ** 2 + (zona.coordenadas[1] - lng) ** 2
    if (d < menor) {
      menor = d
      mejor = zona
    }
  }
  return mejor.nombre
}

/** Agrega a la respuesta del backend lo que usa la interfaz (coordenadas [lat, lng] y barrio). */
function adaptar(tecnico) {
  const coordenadas = [tecnico.latitude, tecnico.longitude]
  return { ...tecnico, coordenadas, zona: zonaCercana(coordenadas) }
}

/**
 * Filtros que el backend no ofrece (texto libre y valoración mínima), aplicados sobre los
 * resultados. Ordena por mejor valoración. Se exporta para probarla.
 */
export function filtrarTecnicos(lista, { texto, valoracionMin } = {}) {
  const buscado = texto?.trim().toLowerCase()
  return lista
    .filter((t) => !valoracionMin || t.rating_average >= Number(valoracionMin))
    .filter(
      (t) =>
        !buscado ||
        `${t.full_name} ${t.specialties.map(nombreEspecialidad).join(' ')} ${t.bio}`
          .toLowerCase()
          .includes(buscado),
    )
    .sort((a, b) => b.rating_average - a.rating_average)
}

/**
 * CU-19. Busca técnicos cerca del barrio elegido (o del centro de Pereira).
 * El backend solo devuelve verificados a quien no es Administrador.
 */
export async function listarTecnicos({ texto, especialidad, zona, valoracionMin } = {}) {
  const [lat, lng] = zona ? ZONAS.find((z) => z.nombre === zona).coordenadas : CENTRO_PEREIRA
  const params = {
    latitude: lat,
    longitude: lng,
    radius_meters: zona ? RADIO_ZONA_METROS : RADIO_CIUDAD_METROS,
    only_verified: true,
  }
  if (especialidad) params.specialty = especialidad
  const { data } = await api.get(`${BASE}/search`, { params })
  return filtrarTecnicos(data.map(adaptar), { texto, valoracionMin })
}

export async function obtenerTecnico(id) {
  const { data } = await api.get(`${BASE}/${id}`)
  return adaptar(data)
}

/** CU-22. El backend arma el enlace de WhatsApp con el número del técnico. */
export async function enlaceWhatsapp(tecnico) {
  const mensaje = `Hola ${tecnico.full_name.split(' ')[0]}, te encontré en OficiosYa Pereira (PrevenRed). ¿Me podrías ayudar con un trabajo?`
  const { data } = await api.get(`${BASE}/${tecnico.id}/whatsapp`, { params: { message: mensaje } })
  return data.whatsapp_url
}

/** CU-17. Perfil propio del técnico; null si todavía no lo ha registrado. */
export async function obtenerMiPerfil() {
  try {
    const { data } = await api.get(`${BASE}/me`)
    return adaptar(data)
  } catch (error) {
    if (error?.response?.status === 404) return null
    throw error
  }
}

/** CU-17. Crea o actualiza el perfil propio. `coordenadas` es [lat, lng]. */
export async function guardarMiPerfil({
  nombre,
  telefono,
  especialidades,
  experiencia,
  bio,
  coordenadas,
}) {
  const { data } = await api.post(`${BASE}/profile`, {
    full_name: nombre.trim(),
    phone_number: telefono.trim(),
    specialties: especialidades,
    experience_years: Number(experiencia),
    bio: bio.trim(),
    latitude: coordenadas[0],
    longitude: coordenadas[1],
  })
  return adaptar(data)
}

/** CU-18. Perfiles que esperan verificación (solo Administrador), los más antiguos primero. */
export async function listarPendientes() {
  const { data } = await api.get(`${BASE}/pending`)
  return data.map(adaptar)
}

/** CU-18. Aprueba (VERIFICADO) o rechaza (RECHAZADO) un perfil. */
export async function verificarTecnico(id, aprobar) {
  const { data } = await api.patch(`${BASE}/${id}/verify`, { approve: aprobar })
  return data
}
