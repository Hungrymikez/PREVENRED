/** Centro de Pereira por defecto (se puede cambiar en .env). */
export const CENTRO_PEREIRA = [
  Number(import.meta.env.VITE_MAP_CENTER_LAT ?? 4.8133),
  Number(import.meta.env.VITE_MAP_CENTER_LNG ?? -75.6961),
]

export const ZOOM_INICIAL = Number(import.meta.env.VITE_MAP_DEFAULT_ZOOM ?? 13)
