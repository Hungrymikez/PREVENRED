import { useQuery } from '@tanstack/react-query'
import { RotateCcw, TrendingDown } from 'lucide-react'
import { useState } from 'react'
import { listarCasos, listarInspectores } from '@/api/casos'
import { Cargando } from '@/components/ui/Estados'
import {
  ATENCION_POR_INSPECTOR,
  equilibrioPendientes,
  horasHastaPendientes,
  pendientesEn,
  reportesPorHora,
  tasaAtencion,
} from '@/utils/ecuaciones'

const HORAS = 48
const num = (n, decimales = 0) =>
  n.toLocaleString('es-CO', { maximumFractionDigits: decimales, minimumFractionDigits: decimales })

/**
 * Proyección de casos pendientes con la EDO dB/dt = λ − μB (ver utils/ecuaciones.js).
 * Toma los datos reales (casos sin resolver, reportes de las últimas 24 h e inspectores
 * activos) y deja simular "¿qué pasa si…?" moviendo λ y el número de inspectores.
 */
export function ProyeccionPendientes({ pendientes }) {
  const casos = useQuery({ queryKey: ['casos', '', false], queryFn: () => listarCasos() })
  const inspectores = useQuery({ queryKey: ['inspectores'], queryFn: listarInspectores })

  return (
    <section
      className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-slate-900"
      aria-labelledby="titulo-proyeccion"
    >
      <h2
        id="titulo-proyeccion"
        className="flex items-center gap-2 text-xl font-bold text-slate-900 dark:text-white"
      >
        <TrendingDown className="size-5" aria-hidden="true" />
        Proyección de casos pendientes
      </h2>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
        Modelo con una ecuación diferencial: cuántos casos sin resolver habrá en las próximas{' '}
        {HORAS} horas según los reportes que llegan y los inspectores que los atienden.
      </p>

      {casos.isPending || inspectores.isPending ? (
        <Cargando texto="Calculando la proyección…" />
      ) : (
        <Simulador
          pendientes={pendientes}
          llegadaReal={casos.data ? reportesPorHora(casos.data) : 0}
          inspectoresReales={inspectores.data?.length ?? 0}
        />
      )}
    </section>
  )
}

function Simulador({ pendientes, llegadaReal, inspectoresReales }) {
  // λ real redondeado a 0,5 para que coincida con el paso del deslizador.
  const llegadaInicial = Math.round(llegadaReal * 2) / 2
  const [llegada, setLlegada] = useState(llegadaInicial)
  const [inspectores, setInspectores] = useState(inspectoresReales)

  const real = {
    inicial: pendientes,
    llegada: llegadaInicial,
    atencion: tasaAtencion(inspectoresReales),
  }
  const simulado = { inicial: pendientes, llegada, atencion: tasaAtencion(inspectores) }
  const equilibrio = equilibrioPendientes(simulado)
  const mitad = horasHastaPendientes(pendientes / 2, simulado)
  const cambiado = llegada !== llegadaInicial || inspectores !== inspectoresReales

  return (
    <div className="mt-4 space-y-5">
      <div className="rounded-xl bg-slate-50 p-4 font-mono text-sm text-slate-800 dark:bg-white/5 dark:text-slate-100">
        <p>dB/dt = λ − μ·B &nbsp;&nbsp;·&nbsp;&nbsp; B(0) = {pendientes}</p>
        <p className="mt-1">
          B(t) = λ/μ + (B₀ − λ/μ)·e<sup>−μt</sup>
          {simulado.atencion > 0 && (
            <>
              {' '}
              = {num(equilibrio, 1)} + ({pendientes} − {num(equilibrio, 1)})·e
              <sup>−{num(simulado.atencion, 2)}t</sup>
            </>
          )}
        </p>
        <p className="mt-2 font-sans text-xs text-slate-600 dark:text-slate-300">
          B = casos pendientes · t = horas · λ = reportes nuevos por hora · μ = inspectores ×{' '}
          {num(ATENCION_POR_INSPECTOR * 100)} % (cada inspector atiende el{' '}
          {num(ATENCION_POR_INSPECTOR * 100)} % de los pendientes por hora)
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Deslizador
          etiqueta="λ · reportes nuevos por hora"
          ayuda={`Real: ${num(llegadaReal, 2)} por hora (últimas 24 h)`}
          valor={llegada}
          min={0}
          max={20}
          paso={0.5}
          onCambio={setLlegada}
        />
        <Deslizador
          etiqueta="Inspectores atendiendo"
          ayuda={`Real: ${inspectoresReales} activos · μ = ${num(simulado.atencion, 2)} por hora`}
          valor={inspectores}
          min={0}
          max={20}
          paso={1}
          onCambio={setInspectores}
        />
      </div>

      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Dato nombre="Pendientes hoy (B₀)" valor={pendientes} />
        <Dato
          nombre="Equilibrio λ/μ"
          valor={Number.isFinite(equilibrio) ? num(equilibrio) : 'Sin límite'}
        />
        <Dato nombre="Pendientes en 24 h" valor={num(pendientesEn(24, simulado))} />
        <Dato
          nombre="Bajar a la mitad"
          valor={mitad === null ? 'No se logra' : `${num(mitad, 1)} h`}
        />
      </dl>

      <Grafica real={real} simulado={simulado} cambiado={cambiado} />

      {cambiado && (
        <button
          type="button"
          onClick={() => {
            setLlegada(llegadaInicial)
            setInspectores(inspectoresReales)
          }}
          className="inline-flex items-center gap-1 text-sm font-medium text-marca-700 hover:underline dark:text-amber-400"
        >
          <RotateCcw className="size-4" aria-hidden="true" />
          Volver a los datos reales
        </button>
      )}
    </div>
  )
}

function Deslizador({ etiqueta, ayuda, valor, min, max, paso, onCambio }) {
  return (
    <label className="block">
      <span className="flex justify-between text-sm font-medium text-slate-800 dark:text-slate-100">
        {etiqueta}
        <span className="text-base font-bold">{num(valor, paso < 1 ? 1 : 0)}</span>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={paso}
        value={valor}
        onChange={(e) => onCambio(Number(e.target.value))}
        className="mt-2 w-full accent-marca-600 dark:accent-amber-500"
      />
      <span className="text-xs text-slate-500 dark:text-slate-400">{ayuda}</span>
    </label>
  )
}

function Dato({ nombre, valor }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3 dark:bg-white/5">
      <dt className="text-xs text-slate-600 dark:text-slate-300">{nombre}</dt>
      <dd className="mt-1 text-2xl font-bold text-slate-900 dark:text-white">{valor}</dd>
    </div>
  )
}

/** Gráfica SVG de B(t): curva simulada, curva con los datos reales y línea de equilibrio. */
function Grafica({ real, simulado, cambiado }) {
  const ancho = 640
  const alto = 240
  const izq = 44
  const abajo = 24
  const puntos = Array.from({ length: HORAS * 2 + 1 }, (_, i) => i / 2)
  const valores = [...puntos.map((t) => pendientesEn(t, simulado))]
  if (cambiado) valores.push(...puntos.map((t) => pendientesEn(t, real)))
  const equilibrio = equilibrioPendientes(simulado)
  if (Number.isFinite(equilibrio)) valores.push(equilibrio)
  const maximo = Math.max(10, ...valores) * 1.1

  const x = (t) => izq + (t / HORAS) * (ancho - izq - 8)
  const y = (b) => alto - abajo - (b / maximo) * (alto - abajo - 8)
  const camino = (modelo) =>
    puntos
      .map((t, i) => `${i ? 'L' : 'M'}${x(t).toFixed(1)} ${y(pendientesEn(t, modelo)).toFixed(1)}`)
      .join(' ')
  const marcasY = [0, 0.25, 0.5, 0.75, 1].map((f) => Math.round((maximo / 1.1) * f))

  return (
    <figure>
      <svg
        viewBox={`0 0 ${ancho} ${alto}`}
        className="w-full"
        role="img"
        aria-label={`Curva de casos pendientes: empieza en ${simulado.inicial} y tiende a ${
          Number.isFinite(equilibrio) ? Math.round(equilibrio) : 'crecer sin límite'
        }`}
      >
        {marcasY.map((m) => (
          <g key={m}>
            <line
              x1={izq}
              x2={ancho - 8}
              y1={y(m)}
              y2={y(m)}
              className="stroke-slate-200 dark:stroke-white/10"
            />
            <text
              x={izq - 6}
              y={y(m) + 4}
              textAnchor="end"
              className="fill-slate-500 text-[11px] dark:fill-slate-400"
            >
              {m}
            </text>
          </g>
        ))}
        {[0, 12, 24, 36, 48].map((t) => (
          <text
            key={t}
            x={x(t)}
            y={alto - 6}
            textAnchor={t === HORAS ? 'end' : 'middle'}
            className="fill-slate-500 text-[11px] dark:fill-slate-400"
          >
            {t} h
          </text>
        ))}
        {Number.isFinite(equilibrio) && equilibrio <= maximo && (
          <>
            <line
              x1={izq}
              x2={ancho - 8}
              y1={y(equilibrio)}
              y2={y(equilibrio)}
              strokeDasharray="6 4"
              className="stroke-amber-600 dark:stroke-amber-400"
            />
            <text
              x={ancho - 10}
              y={y(equilibrio) - 6}
              textAnchor="end"
              className="fill-amber-700 text-[11px] dark:fill-amber-300"
            >
              equilibrio λ/μ = {Math.round(equilibrio)}
            </text>
          </>
        )}
        {cambiado && (
          <path
            d={camino(real)}
            fill="none"
            strokeWidth="2"
            strokeDasharray="4 4"
            className="stroke-slate-400"
          />
        )}
        <path
          d={camino(simulado)}
          fill="none"
          strokeWidth="3"
          className="stroke-marca-600 dark:stroke-amber-400"
        />
        <circle
          cx={x(0)}
          cy={y(simulado.inicial)}
          r="5"
          className="fill-marca-600 dark:fill-amber-400"
        />
      </svg>
      <figcaption className="mt-1 flex flex-wrap gap-x-4 text-xs text-slate-600 dark:text-slate-300">
        <span>
          <span className="mr-1 inline-block h-0.5 w-4 bg-marca-600 align-middle dark:bg-amber-400" />
          {cambiado ? 'Simulación' : 'Proyección con los datos reales'}
        </span>
        {cambiado && (
          <span>
            <span className="mr-1 inline-block h-0.5 w-4 border-t-2 border-dashed border-slate-400 align-middle" />
            Con los datos reales
          </span>
        )}
      </figcaption>
    </figure>
  )
}
