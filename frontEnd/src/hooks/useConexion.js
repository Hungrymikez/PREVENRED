import { useSyncExternalStore } from 'react'

function suscribir(avisar) {
  window.addEventListener('online', avisar)
  window.addEventListener('offline', avisar)
  return () => {
    window.removeEventListener('online', avisar)
    window.removeEventListener('offline', avisar)
  }
}

/** true si el dispositivo tiene conexión. Se actualiza solo cuando se pierde o vuelve la señal. */
export function useConexion() {
  return useSyncExternalStore(suscribir, () => navigator.onLine)
}
