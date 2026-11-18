import { useMutation, useQuery } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { descargarIncidentesCsv, obtenerIndicadoresBienestar, obtenerTablero } from '@/api/admin'
import { ESTADOS_CASO, GRAVEDADES } from '@/api/casos'
import { mensajeDeError } from '@/api/client'
import { Alerta } from '@/components/ui/Alerta'
import { Boton } from '@/components/ui/Boton'
import { Cargando, SinResultados } from '@/components/ui/Estados'
import { ProyeccionPendientes } from './ProyeccionPendientes'

/** B₀ del modelo: todos los incidentes que todavía no están en estado RESUELTO. */
function casosSinResolver({ total_incidents, incidents_by_status = {} }) {
  return total_incidents - (incidents_by_status.RESUELTO ?? 0)
}

const HABITABILIDAD = {
  HABITABLE: 'Habitable',
  RESTRINGIDO: 'Uso restringido',
  EVACUACION: 'Evacuación',
}

/**
 * Tablero del Administrador.
 * - CU-45 Tablero municipal: incidentes, inspecciones, ayudas y voluntariado.
 * - CU-26 Indicadores de bienestar por barrio (solo agregados, nunca respuestas individuales).
 * - CU-46 Exportar los incidentes en CSV.
 */
export default function Tablero() {
  const tablero = useQuery({ queryKey: ['admin', 'tablero'], queryFn: obtenerTablero })
  const exportar = useMutation({ mutationFn: descargarIncidentesCsv })

  return (
    <>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Tablero municipal</h1>
          <p className="mt-1 text-slate-600 dark:text-slate-300">
            Indicadores oficiales de la ciudad, actualizados con cada consulta.
          </p>
        </div>
        <Boton
          type="button"
          variante="secundario"
          cargando={exportar.isPending}
          onClick={() => exportar.mutate()}
        >
          {!exportar.isPending && <Download className="size-4" aria-hidden="true" />}
          Descargar CSV de incidentes
        </Boton>
      </div>

      <div className="mt-4 space-y-2" aria-live="polite">
        {exportar.error && <Alerta tipo="error">{mensajeDeError(exportar.error)}</Alerta>}
        {exportar.isSuccess && <Alerta tipo="exito">Descargado: {exportar.data}</Alerta>}
      </div>

      <div className="mt-5">
        {tablero.isPending ? (
          <Cargando texto="Cargando indicadores…" />
        ) : tablero.error ? (
          <Alerta tipo="error">{mensajeDeError(tablero.error)}</Alerta>
        ) : (
          <>
            <ResumenMunicipal datos={tablero.data} />
            <ProyeccionPendientes pendientes={casosSinResolver(tablero.data)} />
          </>
        )}
      </div>

      <IndicadoresBienestar />
    </>
  )
}

/** CU-45. Tarjetas con los totales y barras simples con el desglose. */
function ResumenMunicipal({ datos }) {
  const tarjetas = [
    ['Incidentes reportados', datos.total_incidents],
    ['Inspecciones de inmuebles', datos.total_inspections],
    ['Necesidades de ayuda', datos.total_aid_needs],
    ['Ofertas de ayuda', datos.total_aid_offers],
    ['Donaciones emparejadas', datos.total_matches],
    ['Voluntarios disponibles', datos.active_volunteers],
  ]

  return (
    <div className="space-y-5">
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {tarjetas.map(([nombre, valor]) => (
          <div
            key={nombre}
            className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900"
          >
            <dt className="text-sm text-slate-600 dark:text-slate-300">{nombre}</dt>
            <dd className="mt-1 text-3xl font-bold text-slate-900 dark:text-white">{valor}</dd>
          </div>
        ))}
      </dl>

      <div className="grid gap-4 md:grid-cols-3">
        <Desglose
          titulo="Incidentes por estado"
          conteos={datos.incidents_by_status}
          nombres={ESTADOS_CASO}
        />
        <Desglose
          titulo="Incidentes por gravedad"
          conteos={datos.incidents_by_severity}
          nombres={GRAVEDADES}
        />
        <Desglose
          titulo="Inmuebles por habitabilidad"
          conteos={datos.inspections_by_habitability}
          nombres={HABITABILIDAD}
        />
      </div>
    </div>
  )
}

/** Barras horizontales hechas con divs: el ancho es proporcional al total del grupo. */
function Desglose({ titulo, conteos = {}, nombres }) {
  const filas = Object.entries(conteos).sort((a, b) => b[1] - a[1])
  const total = filas.reduce((suma, [, n]) => suma + n, 0)

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900">
      <h2 className="font-semibold text-slate-900 dark:text-white">{titulo}</h2>
      {filas.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Sin datos todavía.</p>
      ) : (
        <ul className="mt-3 space-y-2" aria-label={titulo}>
          {filas.map(([clave, n]) => (
            <li key={clave}>
              <div className="flex justify-between text-sm text-slate-700 dark:text-slate-200">
                <span>{nombres[clave] ?? clave}</span>
                <span className="font-medium">{n}</span>
              </div>
              <div
                className="mt-1 h-2 rounded-full bg-slate-100 dark:bg-white/10"
                aria-hidden="true"
              >
                <div
                  className="h-2 rounded-full bg-marca-600 dark:bg-amber-500"
                  style={{ width: `${total ? (n / total) * 100 : 0}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

/** CU-26. Promedio de ánimo (1 a 5) por barrio, con 3 o más respuestas (k-anonimato, RF-17). */
function IndicadoresBienestar() {
  const {
    data: indicadores = [],
    isPending,
    error,
  } = useQuery({ queryKey: ['admin', 'bienestar'], queryFn: obtenerIndicadoresBienestar })

  return (
    <section className="mt-8" aria-labelledby="titulo-bienestar">
      <h2 id="titulo-bienestar" className="text-xl font-bold text-slate-900 dark:text-white">
        Bienestar emocional por barrio
      </h2>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
        Promedio de ánimo de 1 (muy mal) a 5 (muy bien). Solo se muestran barrios con 3 o más
        respuestas, para proteger la identidad de las personas.
      </p>

      <div className="mt-4">
        {isPending ? (
          <Cargando texto="Cargando indicadores de bienestar…" />
        ) : error ? (
          <Alerta tipo="error">{mensajeDeError(error)}</Alerta>
        ) : indicadores.length === 0 ? (
          <SinResultados titulo="Aún no hay indicadores">
            Ningún barrio alcanza todavía el mínimo de respuestas para publicarse.
          </SinResultados>
        ) : (
          <ul className="space-y-3">
            {indicadores.map((item) => (
              <li
                key={item.neighborhood}
                className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="font-semibold text-slate-900 dark:text-white">
                    {item.neighborhood}
                  </h3>
                  <p className="text-sm text-slate-600 dark:text-slate-300">
                    {item.sample_count} respuestas
                    {item.crisis_alerts > 0 && (
                      <span className="ml-2 font-medium text-alerta-700 dark:text-red-300">
                        · {item.crisis_alerts}{' '}
                        {item.crisis_alerts === 1 ? 'alerta de crisis' : 'alertas de crisis'}
                      </span>
                    )}
                  </p>
                </div>
                <div className="mt-2 flex items-center gap-3">
                  <div
                    className="h-2 flex-1 rounded-full bg-slate-100 dark:bg-white/10"
                    aria-hidden="true"
                  >
                    <div
                      className="h-2 rounded-full bg-marca-600 dark:bg-amber-500"
                      style={{ width: `${(item.average_mood / 5) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-900 dark:text-white">
                    Ánimo {item.average_mood.toFixed(1)} / 5
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
