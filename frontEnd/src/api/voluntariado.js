/**
 * Voluntariado (M12 · volunteering). Conectado al backend real:
 *  - CU-44 Inscribirse como voluntario -> POST /volunteering/register (crea o actualiza el perfil)
 *  - CU-44 Mi perfil de voluntario      -> GET  /volunteering/me (404 si aún no se inscribe)
 *  - CU-38 Mis asignaciones             -> GET  /volunteering/assignments/my
 *  - CU-43 Voluntarios disponibles      -> GET  /volunteering/volunteers (admin o inspector)
 *  - CU-43 Asignar voluntario           -> POST /volunteering/assign (admin o inspector)
 */
import { api } from '@/api/client'

/** Habilidades (VolunteerSkill del backend). */
export const HABILIDADES = {
  PRIMEROS_AUXILIOS: 'Primeros auxilios',
  RESCATE: 'Rescate',
  LOGISTICA: 'Logística',
  APOYO_PSICOLOGICO: 'Apoyo psicológico',
  CONDUCCION: 'Conducción',
  REMOCION_ESCOMBROS: 'Remoción de escombros',
  OTRO: 'Otro',
}

/** Estados de una asignación (AssignmentStatus del backend). */
export const ESTADOS_ASIGNACION = {
  ASIGNADO: 'Asignada',
  EN_CAMINO: 'En camino',
  COMPLETADO: 'Completada',
  CANCELADO: 'Cancelada',
}

/** Perfil propio o `null` si la persona todavía no se ha inscrito. */
export async function obtenerMiPerfil() {
  try {
    const { data } = await api.get('/volunteering/me')
    return data
  } catch (error) {
    if (error?.response?.status === 404) return null
    throw error
  }
}

/** `ubicacion` es [lat, lng]. Si ya existe el perfil, el backend lo actualiza. */
export async function inscribirVoluntario({ nombre, telefono, habilidades, ubicacion }) {
  const { data } = await api.post('/volunteering/register', {
    full_name: nombre.trim(),
    phone_number: telefono.trim(),
    skills: habilidades,
    latitude: ubicacion[0],
    longitude: ubicacion[1],
  })
  return data
}

export async function listarMisAsignaciones() {
  const { data } = await api.get('/volunteering/assignments/my')
  return data
}

export async function listarVoluntarios() {
  const { data } = await api.get('/volunteering/volunteers')
  return data
}

export async function asignarVoluntario({ voluntarioId, casoId, tarea }) {
  const { data } = await api.post('/volunteering/assign', {
    volunteer_id: voluntarioId,
    incident_id: casoId,
    task_description: tarea.trim(),
  })
  return data
}
