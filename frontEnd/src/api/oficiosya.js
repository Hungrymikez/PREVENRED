/**
 * OficiosYa (CU-19, CU-22). DATOS DE PRUEBA: cuando el backend tenga el módulo services,
 * cada función pasa a llamar a la API (ej.: api.get('/technicians', { params: filtros })).
 */
import { RESENAS, TECNICOS } from '@/api/mocks/datos'
import { simularRed } from '@/api/mocks/simular'
import { coordenadasDeZona } from '@/utils/zonas'

export const ESPECIALIDADES = [
  'Albañilería',
  'Carpintería',
  'Electricidad',
  'Gas',
  'Pintura',
  'Plomería',
  'Techos',
]

/** Solo técnicos VERIFICADOS (regla de CU-19). Se exporta para probarla. */
export function filtrarTecnicos(lista, filtros = {}) {
  const { texto, especialidad, zona, valoracionMin, soloDisponibles } = filtros
  const buscado = texto?.trim().toLowerCase()

  return lista
    .filter((t) => t.verificationStatus === 'VERIFICADO')
    .filter((t) => !especialidad || t.specialties.includes(especialidad))
    .filter((t) => !zona || t.zona === zona)
    .filter((t) => !valoracionMin || t.rating >= Number(valoracionMin))
    .filter((t) => !soloDisponibles || t.disponible)
    .filter(
      (t) =>
        !buscado ||
        `${t.fullName} ${t.specialties.join(' ')} ${t.bio}`.toLowerCase().includes(buscado),
    )
    .map((t) => ({ ...t, coordenadas: coordenadasDeZona(t.zona) }))
    .sort((a, b) => b.rating - a.rating)
}

export function listarTecnicos(filtros) {
  return simularRed(filtrarTecnicos(TECNICOS, filtros))
}

export async function obtenerTecnico(id) {
  const tecnico = TECNICOS.find((t) => t.id === id && t.verificationStatus === 'VERIFICADO')
  if (!tecnico) throw new Error('El técnico no existe o no está verificado.')
  return simularRed({
    ...tecnico,
    coordenadas: coordenadasDeZona(tecnico.zona),
    resenas: RESENAS.filter((r) => r.targetId === id),
  })
}

/**
 * CU-22. La plataforma solo registra el contacto mínimo (usuario, técnico y fecha)
 * y arma el enlace con un mensaje inicial sin datos personales innecesarios.
 */
export async function enlaceWhatsapp(tecnico) {
  // Versión real: await api.post(`/technicians/${tecnico.id}/contact`)
  const mensaje = `Hola ${tecnico.fullName.split(' ')[0]}, te encontré en OficiosYa Pereira (PrevenRed). ¿Me podrías ayudar con un trabajo?`
  return simularRed(`https://wa.me/${tecnico.phone}?text=${encodeURIComponent(mensaje)}`, 200)
}
