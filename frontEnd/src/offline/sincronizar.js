import { mensajeDeError } from '@/api/client'
import { crearReporte } from '@/api/incidentes'
import { eliminarPendiente, listarPendientes, marcarError } from './almacen'

let enCurso = null

/**
 * Envía los reportes guardados sin conexión, en el orden en que se hicieron (CU-37 pasos 4-8).
 * Si ya hay una sincronización en marcha, devuelve esa misma (no se envía nada dos veces).
 */
export function sincronizarPendientes() {
  enCurso ??= enviarEnOrden().finally(() => {
    enCurso = null
  })
  return enCurso
}

async function enviarEnOrden() {
  const pendientes = (await listarPendientes()).filter((p) => p.estado === 'pendiente')
  let enviados = 0

  for (const { clientId, creadoEn, datos } of pendientes) {
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
