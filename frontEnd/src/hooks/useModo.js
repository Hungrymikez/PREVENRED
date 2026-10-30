import { useQuery } from '@tanstack/react-query'
import { obtenerModo } from '@/api/modo'

/**
 * Modo vigente de la plataforma. Se vuelve a consultar cada minuto y al recuperar la conexión,
 * así la interfaz se reconfigura sola cuando un administrador activa la emergencia (RF-02, CU-04 A3).
 */
export function useModo() {
  const { data: modo, isPending } = useQuery({
    queryKey: ['modo'],
    queryFn: obtenerModo,
    refetchInterval: 60_000,
  })

  return { modo, cargando: isPending, enEmergencia: modo?.mode === 'EMERGENCIA' }
}
