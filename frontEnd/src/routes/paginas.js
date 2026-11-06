/**
 * Cargadores de las páginas que deben funcionar sin conexión en una emergencia.
 * App.jsx los usa con lazy(); precargarModoEmergencia() los descarga por adelantado
 * para que el service worker los guarde mientras hay señal.
 */
export const cargarPanel = () => import('@/pages/Panel')
export const cargarEmergencia = () => import('@/pages/emergencia/Emergencia')
export const cargarReportar = () => import('@/pages/emergencia/Reportar')
export const cargarMisCasos = () => import('@/pages/emergencia/MisCasos')
export const cargarDetalleCaso = () => import('@/pages/emergencia/DetalleCaso')

export function precargarModoEmergencia() {
  return Promise.all([
    cargarPanel(),
    cargarEmergencia(),
    cargarReportar(),
    cargarMisCasos(),
    cargarDetalleCaso(),
  ]).catch(() => {
    // Si falla (sin red), se intentará en la próxima visita.
  })
}
