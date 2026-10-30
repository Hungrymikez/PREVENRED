import { useQuery } from '@tanstack/react-query'
import { listarPendientes } from '@/offline/almacen'

/** Reportes guardados en el dispositivo que aún no llegan al servidor (CU-37 paso 3). */
export function usePendientes() {
  return useQuery({
    queryKey: ['pendientes'],
    queryFn: listarPendientes,
    networkMode: 'always', // se leen del dispositivo: funcionan sin conexión
  })
}
