/** 2026-10-29T14:05 -> "29 oct, 2:05 p. m." */
export function formatearFecha(iso) {
  return new Date(iso).toLocaleString('es-CO', {
    day: 'numeric',
    month: 'short',
    hour: 'numeric',
    minute: '2-digit',
  })
}
