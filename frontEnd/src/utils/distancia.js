const RADIO_TIERRA_KM = 6371

/** Distancia en km entre dos puntos [lat, lng] (fórmula de Haversine). */
export function distanciaKm([lat1, lng1], [lat2, lng2]) {
  const rad = (grados) => (grados * Math.PI) / 180
  const dLat = rad(lat2 - lat1)
  const dLng = rad(lng2 - lng1)
  const a =
    Math.sin(dLat / 2) ** 2 + Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(dLng / 2) ** 2
  return 2 * RADIO_TIERRA_KM * Math.asin(Math.sqrt(a))
}

/** 0.05 -> "a menos de 100 m" · 0.42 -> "a 420 m" · 2.345 -> "a 2,3 km" */
export function formatearDistancia(km) {
  if (km < 0.1) return 'a menos de 100 m'
  if (km < 1) return `a ${Math.round(km * 100) * 10} m`
  return `a ${km.toLocaleString('es-CO', { maximumFractionDigits: 1 })} km`
}

/** 25000 -> "$25.000" */
export function formatearPesos(valor) {
  return valor.toLocaleString('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  })
}
