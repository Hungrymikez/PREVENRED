import { mensajeDeError } from '@/api/client'
import { crearReporte } from '@/api/incidentes'
import { eliminarPendiente, listarPendientes, marcarError } from './almacen'

const enCurso = new Map()

/**
 * Envía los reportes que `usuarioId` guardó sin conexión, en el orden en que se hicieron
 * (CU-37 pasos 4-8). Si ya hay una sincronización suya en marcha, devuelve esa misma
 * (no se envía nada dos veces).
 * `sigueActivo()` dice si la sesión sigue siendo de esa persona: si cambia a mitad de
 * camino (cerró sesión y entró otra), se detiene para no enviar sus reportes con otra cuenta.
 */
export function sincronizarPendientes(usuarioId, { sigueActivo = () => true } = {}) {
  if (!enCurso.has(usuarioId)) {
    const promesa = enviarEnOrden(usuarioId, sigueActivo).finally(() => {
      enCurso.delete(usuarioId)
    })
    enCurso.set(usuarioId, promesa)
  }
  return enCurso.get(usuarioId)
}

async function enviarEnOrden(usuarioId, sigueActivo) {
  const pendientes = (await listarPendientes(usuarioId)).filter((p) => p.estado === 'pendiente')
  let enviados = 0

  for (const { clientId, creadoEn, datos } of pendientes) {
    if (!sigueActivo()) break
    try {
      // El clientId hace que el servidor no lo duplique aunque se reintente (H-07).
      await crearReporte({ ...datos, clientId, reportedAt: creadoEn })
      await eliminarPendiente(clientId)
      enviados += 1
    } catch (error) {
      const estado = error?.response?.status
      // Sin red (A2) o sesión vencida (E3): se detiene y la cola se conserva para después.
      if (!error?.response || estado === 401) break
      // El servidor lo rechazó (E1): se marca para revisión y se sigue con los demás.
      await marcarError(clientId, mensajeDeError(error))
    }
  }
  return enviados
}
