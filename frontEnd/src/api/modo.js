/**
 * Modo operacional global: Cotidiano o Emergencia (CU-04, RF-01, RF-02).
 * DATOS DE PRUEBA: la versión real lo consulta al backend (ej.: api.get('/operating-mode')).
 * Solo un Administrador cambia el modo; aquí se puede simular en desarrollo.
 */
import { simularRed } from '@/api/mocks/simular'

const CLAVE_DEMO = 'prevenred_modo_demo'

export const TIPOS_EVENTO = {
  SISMO: 'Sismo',
  INUNDACION: 'Inundación',
  DESLIZAMIENTO: 'Deslizamiento',
}

const COTIDIANO = { mode: 'COTIDIANO' }

function leer() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE_DEMO)) ?? COTIDIANO
  } catch {
    return COTIDIANO
  }
}

export function obtenerModo() {
  return simularRed(leer(), 200)
}

/** SOLO PARA DEMOSTRACIÓN. En la versión real lo hace el Administrador con MFA (CU-04). */
export function simularCambioDeModo(activarEmergencia) {
  const modo = activarEmergencia
    ? {
        mode: 'EMERGENCIA',
        eventType: 'SISMO',
        reason: 'Sismo de magnitud 5,8 sentido en Pereira. Reporta daños y pide ayuda aquí.',
        startedAt: new Date().toISOString(),
      }
    : COTIDIANO
  try {
    localStorage.setItem(CLAVE_DEMO, JSON.stringify(modo))
  } catch {
    // Sin almacenamiento: el cambio no se conserva al recargar.
  }
  return simularRed(modo, 200)
}
