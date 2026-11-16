import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/hooks/useAuth'
import { listarPendientes } from '@/offline/almacen'

/**
 * Reportes de la persona con sesión guardados en el dispositivo que aún no llegan al
 * servidor (CU-37 paso 3). Nunca muestra los de otra cuenta del mismo celular.
 */
export function usePendientes() {
  const usuarioId = useAuth().usuario?.id
  return useQuery({
    queryKey: ['pendientes', usuarioId],
    queryFn: () => listarPendientes(usuarioId),
    enabled: Boolean(usuarioId),
    networkMode: 'always', // se leen del dispositivo: funcionan sin conexión
  })
}
