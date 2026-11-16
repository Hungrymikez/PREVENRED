/**
 * Bandeja de casos del personal de atención (CU-39 Gestionar incidentes).
 * Conectada al backend real: el Inspector y el Administrador ven todos los casos
 * (GET /incidents/); el Administrador los asigna a un Inspector (PATCH .../assign) y
 * cambia el estado de cualquiera; el Inspector, solo de los suyos (PATCH .../status).
 */
import { api } from '@/api/client'

/** Estados del ciclo de vida en el backend, en orden. */
export const ESTADOS_CASO = {
  REPORTADO: 'Reportado',
  EN_REVISION: 'En revisión',
  ASIGNADO: 'Asignado',
  EN_ATENCION: 'En atención',
  RESUELTO: 'Resuelto',
}

export const TIPOS_CASO = {
  VIA_BLOQUEADA: 'Vía bloqueada',
  DESLIZAMIENTO: 'Deslizamiento',
  INUNDACION: 'Inundación',
  DANO_ESTRUCTURAL: 'Daño estructural',
  VIVIENDA_DANADA: 'Vivienda dañada',
  OTRO: 'Otro',
}

export const GRAVEDADES = {
  BAJA: 'Baja',
  MEDIA: 'Media',
  ALTA: 'Alta',
  CRITICA: 'Crítica',
}

/**
 * Casos más recientes primero. `estado` filtra por uno de ESTADOS_CASO y `asignadosAMi`
 * deja solo los asignados a quien consulta (vista del Inspector).
 */
export async function listarCasos({ estado, asignadosAMi = false } = {}) {
  const params = { limit: 100 }
  if (estado) params.status = estado
  if (asignadosAMi) params.assigned_to_me = true
  const { data } = await api.get('/incidents/', { params })
  return data
}

export async function cambiarEstadoCaso(id, { estado, notas }) {
  const { data } = await api.patch(`/incidents/${id}/status`, {
    new_status: estado,
    notes: notas ?? '',
  })
  return data
}

/** CU-39: el Administrador asigna el caso a un Inspector (pasa a "Asignado"). */
export async function asignarCaso(id, { inspectorId, notas }) {
  const { data } = await api.patch(`/incidents/${id}/assign`, {
    assignee_id: inspectorId,
    notes: notas ?? '',
  })
  return data
}

/** Inspectores activos, para elegir a quién asignar (solo Administrador). */
export async function listarInspectores() {
  const { data } = await api.get('/auth/users', { params: { role: 'inspector' } })
  return data
}
