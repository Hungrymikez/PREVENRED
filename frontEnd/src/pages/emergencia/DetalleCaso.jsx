import { useQuery } from '@tanstack/react-query'
import { Check } from 'lucide-react'
import { useParams } from 'react-router'
import { Marker } from 'react-leaflet'
import {
  CATEGORIAS_REPORTE,
  ESTADOS,
  nombreEstado,
  nombreTipo,
  obtenerCaso,
} from '@/api/incidentes'
import { Mapa } from '@/components/mapa/Mapa'
import { Cargando, ErrorAlCargar } from '@/components/ui/Estados'
import { Volver } from '@/components/ui/Volver'
import { formatearFecha } from '@/utils/fechas'
import { EstadoCaso } from './EstadoCaso'

/** CU-32 pasos 2-3: estado autorizado del caso y su historial de cambios. */
export default function DetalleCaso() {
  const { caseId } = useParams()
  const {
    data: caso,
    isPending,
    error,
  } = useQuery({
    queryKey: ['caso', caseId],
    queryFn: () => obtenerCaso(caseId),
    networkMode: 'offlineFirst',
  })

  return (
    <>
      <Volver a="/emergencia/casos">Volver a mis casos</Volver>
      <div className="mt-4">
        {isPending ? (
          <Cargando />
        ) : error ? (
          <ErrorAlCargar error={error} />
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="rounded-2xl bg-white p-6 shadow-sm">
              <p className="font-mono text-sm font-semibold text-slate-500">{caso.caseId}</p>
              <h1 className="mt-1 text-2xl font-bold text-slate-900">{nombreTipo(caso)}</h1>
              <p className="text-slate-600">{CATEGORIAS_REPORTE[caso.categoria].titulo}</p>
              <div className="mt-3">
                <EstadoCaso caso={caso} />
              </div>
              {caso.quantity && (
                <p className="mt-3 text-slate-700">Para {caso.quantity} personas</p>
              )}
              {caso.description && <p className="mt-3 text-slate-700">{caso.description}</p>}

              <h2 className="mt-6 font-semibold text-slate-900">Seguimiento</h2>
              <LineaDeTiempo caso={caso} />
            </section>

            <section aria-label="Ubicación del caso">
              <Mapa centro={caso.coordenadas} zoom={15} className="h-72">
                <Marker position={caso.coordenadas} />
              </Mapa>
            </section>
          </div>
        )}
      </div>
    </>
  )
}

/** Los 5 estados en orden; los alcanzados muestran su fecha y nota (RF-24). */
function LineaDeTiempo({ caso }) {
  return (
    <ol className="mt-3 space-y-0">
      {ESTADOS.map((estado, i) => {
        const cambio = caso.historial.find((h) => h.toStatus === estado)
        const ultimo = i === ESTADOS.length - 1
        return (
          <li key={estado} className="relative flex gap-3 pb-5 last:pb-0">
            {!ultimo && (
              <span
                className={`absolute top-6 left-3 h-full w-0.5 -translate-x-1/2 ${cambio ? 'bg-green-600' : 'bg-slate-200'}`}
                aria-hidden="true"
              />
            )}
            <span
              className={`relative flex size-6 shrink-0 items-center justify-center rounded-full ${
                cambio ? 'bg-green-600 text-white' : 'border-2 border-slate-300 bg-white'
              }`}
              aria-hidden="true"
            >
              {cambio && <Check className="size-4" />}
            </span>
            <div>
              <p className={`font-medium ${cambio ? 'text-slate-900' : 'text-slate-400'}`}>
                {nombreEstado(estado, caso.categoria)}
                <span className="sr-only">{cambio ? ' (completado)' : ' (pendiente)'}</span>
              </p>
              {cambio && (
                <p className="text-xs text-slate-500">{formatearFecha(cambio.changedAt)}</p>
              )}
              {cambio?.note && <p className="mt-1 text-sm text-slate-700">{cambio.note}</p>}
            </div>
          </li>
        )
      })}
    </ol>
  )
}
