/**
 * Modo operacional global: Cotidiano o Emergencia (CU-04, RF-01, RF-02).
 * Se consulta al backend (GET /mode/current, público) y solo un Administrador lo cambia
 * (POST /mode/switch, RN-01). El backend guarda el historial de cambios (RN-02).
 */
import { api } from '@/api/client'

export const TIPOS_EVENTO = {
  SISMO: 'Sismo',
  INUNDACION: 'Inundación',
  DESLIZAMIENTO: 'Deslizamiento',
}

/** Respuesta del backend -> forma que usa la app ({ mode, reason, startedAt }). */
function aModo(data) {
  return { mode: data.mode, reason: data.reason, startedAt: data.created_at }
}

export async function obtenerModo() {
  const { data } = await api.get('/mode/current')
  return aModo(data)
}

/** CU-04. `motivo` es obligatorio (mínimo 10 caracteres) y queda en el historial. */
export async function cambiarModo({ activarEmergencia, motivo }) {
  const { data } = await api.post('/mode/switch', {
    new_mode: activarEmergencia ? 'EMERGENCIA' : 'COTIDIANO',
    reason: motivo,
  })
  return aModo(data)
}
