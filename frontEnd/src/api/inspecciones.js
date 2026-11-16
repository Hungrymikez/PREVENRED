/**
 * Censo e inspección de inmuebles (M10 · fieldwork). Conectado al backend real:
 *  - CU-35 Consultar inspecciones -> GET  /fieldwork/inspections (inspector: las suyas; admin: todas)
 *  - CU-34/CU-36 Registrar censo  -> POST /fieldwork/inspections (colección property_inspections)
 */
import { api } from '@/api/client'

/** Nivel de daño del inmueble (DamageLevel del backend). */
export const NIVELES_DANO = {
  LEVE: 'Leve',
  MODERADO: 'Moderado',
  SEVERO: 'Severo',
  DESTRUIDO: 'Destruido',
}

/** Resultado de habitabilidad (HabitabilityStatus del backend). */
export const HABITABILIDAD = {
  HABITABLE: 'Habitable',
  RESTRINGIDO: 'Uso restringido',
  EVACUACION: 'Evacuación',
}

export async function listarInspecciones() {
  const { data } = await api.get('/fieldwork/inspections', { params: { limit: 100 } })
  return data
}

/**
 * Registra la inspección. `ubicacion` es [lat, lng] (como la entrega SelectorUbicacion).
 * Si viene de un caso (`caso`), se deja la referencia en las notas técnicas: el backend
 * todavía no guarda el incidente relacionado en property_inspections.
 */
export async function registrarInspeccion({
  direccion,
  barrio,
  residentes,
  nivelDano,
  habitabilidad,
  notas = '',
  ubicacion,
  fotos = [],
  caso,
}) {
  const referencia = caso ? `[Caso ${caso}] ` : ''
  const { data } = await api.post('/fieldwork/inspections', {
    property_address: direccion.trim(),
    neighborhood: barrio.trim(),
    residents_count: Number(residentes),
    damage_level: nivelDano,
    habitability: habitabilidad,
    technical_notes: `${referencia}${notas.trim()}`.trim(),
    latitude: ubicacion[0],
    longitude: ubicacion[1],
    photos: fotos,
  })
  return data
}
