import { useQuery } from '@tanstack/react-query'
import { obtenerModo } from '@/api/modo'

const CLAVE_ULTIMO_MODO = 'prevenred_ultimo_modo'

function leerUltimoModo() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE_ULTIMO_MODO)) ?? undefined
  } catch {
    return undefined
  }
}

async function consultarYRecordar() {
  const modo = await obtenerModo()
  try {
    localStorage.setItem(CLAVE_ULTIMO_MODO, JSON.stringify(modo))
  } catch {
    // Sin almacenamiento: solo se pierde el recuerdo para abrir sin conexión.
  }
  return modo
}

/**
 * Modo vigente de la plataforma. Se vuelve a consultar cada minuto y al recuperar la conexión,
 * así la interfaz se reconfigura sola cuando un administrador activa la emergencia (RF-02, CU-04 A3).
 * Sin conexión se usa el último modo conocido: así se puede reportar aunque la app abra sin señal.
 */
export function useModo() {
  const { data: modo, isPending } = useQuery({
    queryKey: ['modo'],
    queryFn: consultarYRecordar,
    initialData: leerUltimoModo,
    initialDataUpdatedAt: 0, // el recuerdo se toma como viejo: se consulta apenas haya red
    networkMode: 'offlineFirst',
    refetchInterval: 60_000,
  })

  return { modo, cargando: isPending, enEmergencia: modo?.mode === 'EMERGENCIA' }
}
