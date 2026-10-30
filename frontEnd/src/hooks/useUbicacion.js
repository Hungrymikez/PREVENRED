import { useState } from 'react'

/**
 * Pide la ubicación al GPS del dispositivo (CU-48). Solo se usa si la persona lo autoriza.
 * Si falla o no la permite, se puede marcar a mano en el mapa.
 * Uso: const gps = useUbicacion(); gps.pedir((coordenadas) => ...)
 */
export function useUbicacion() {
  const [buscando, setBuscando] = useState(false)
  const [error, setError] = useState('')

  function pedir(alEncontrar) {
    if (!navigator.geolocation) {
      setError('Tu dispositivo no permite usar el GPS.')
      return
    }
    setBuscando(true)
    setError('')
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setBuscando(false)
        alEncontrar([coords.latitude, coords.longitude])
      },
      () => {
        setBuscando(false)
        setError('No pudimos obtener tu ubicación.')
      },
      { enableHighAccuracy: true, timeout: 10_000 },
    )
  }

  return { buscando, error, pedir }
}
