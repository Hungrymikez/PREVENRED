import { useQueryClient } from '@tanstack/react-query'
import { CloudOff, RefreshCw, TriangleAlert } from 'lucide-react'
import { useEffect } from 'react'
import { Link } from 'react-router'
import { useConexion } from '@/hooks/useConexion'
import { usePendientes } from '@/hooks/usePendientes'
import { sincronizarPendientes } from '@/offline/sincronizar'

const REINTENTO_MS = 30_000

/**
 * Indica si no hay conexión y envía solos los reportes guardados cuando vuelve la señal
 * (CU-37 pasos 1, 4 y 8). Si la conexión es intermitente, reintenta cada 30 s (A2).
 */
export function Sincronizador() {
  const enLinea = useConexion()
  const queryClient = useQueryClient()
  const { data: pendientes = [] } = usePendientes()
  const porEnviar = pendientes.filter((p) => p.estado === 'pendiente').length
  const conError = pendientes.length - porEnviar

  useEffect(() => {
    if (!enLinea || porEnviar === 0) return undefined
    const sincronizar = () =>
      sincronizarPendientes().then(() => {
        queryClient.invalidateQueries({ queryKey: ['pendientes'] })
        queryClient.invalidateQueries({ queryKey: ['mis-casos'] })
      })
    sincronizar()
    const id = setInterval(sincronizar, REINTENTO_MS)
    return () => clearInterval(id)
  }, [enLinea, porEnviar, queryClient])

  if (!enLinea) {
    return (
      <Aviso Icono={CloudOff} estilo="bg-amber-100 text-amber-950">
        <strong>Sin conexión.</strong> Tus reportes se guardan en este celular y se envían solos al
        volver la señal.
        {porEnviar > 0 && ` Pendientes: ${porEnviar}.`}
      </Aviso>
    )
  }
  if (porEnviar > 0) {
    return (
      <Aviso Icono={RefreshCw} estilo="bg-marca-50 text-marca-900" girando>
        Enviando {porEnviar === 1 ? '1 reporte guardado' : `${porEnviar} reportes guardados`}…
      </Aviso>
    )
  }
  if (conError > 0) {
    return (
      <Aviso Icono={TriangleAlert} estilo="bg-alerta-50 text-alerta-700">
        {conError === 1
          ? '1 reporte no se pudo enviar.'
          : `${conError} reportes no se pudieron enviar.`}{' '}
        <Link to="/emergencia/casos" className="font-semibold underline">
          Revisar
        </Link>
      </Aviso>
    )
  }
  return null
}

function Aviso({ Icono, estilo, girando = false, children }) {
  return (
    <div className={estilo} role="status">
      <p className="mx-auto flex max-w-5xl items-center gap-2 px-4 py-2 text-sm">
        <Icono className={`size-4 shrink-0 ${girando ? 'animate-spin' : ''}`} aria-hidden="true" />
        <span>{children}</span>
      </p>
    </div>
  )
}
